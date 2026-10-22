import os
import tempfile
import requests
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from celery import shared_task
from bot.config import BOT_TOKEN
from .models import Newsletter

User = get_user_model()

@shared_task(name='email_sender')
def send_email_task(email, title, body, image_url=None, unsubscribe_url='#'):
    try:
        context = {
            'title': title,
            'body': body,
            'email': email,
            'logo_url': f"{settings.BASE_URL}/static/images/logo.png",
            'image_url_public': image_url,
            'unsubscribe_url': unsubscribe_url,
        }

        html_content = render_to_string('emails/letter.html', context)

        msg = EmailMessage(
            subject=title,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        msg.content_subtype = 'html'

        if image_url and image_url.startswith('http'):
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_url)[-1]) as temp_file:
                        temp_file.write(response.content)
                        temp_file_path = temp_file.name
                    
                    msg.attach_file(temp_file_path)
                    try:
                        msg.send()
                    finally:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                    return f'Лист успішно надіслано на {email}'
            except Exception:
                pass

        msg.send()
        return f'Лист успішно надіслано на {email}'
        
    except Exception as e:
        raise Exception(f'Помилка відправки email на {email}: {str(e)}')


@shared_task(name='tgmessage_sender', bind=True, max_retries=3, default_retry_delay=10)
def send_telegram_message_task(self, chat_id: int, message: str, image_url=None):
    try:
        if image_url:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
            payload = {
                'chat_id': chat_id,
                'caption': message,
                'parse_mode': 'html',
            }
            img_response = requests.get(image_url, timeout=10)
            
            if img_response.status_code == 200:
                files = {'photo': ('photo.jpg', img_response.content, 'image/jpeg')}
                response = requests.post(url, data=payload, files=files, timeout=15)
            else:
                url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
                payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'html'}
                response = requests.post(url, json=payload, timeout=10)
        else:
            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
            payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'html'}
            response = requests.post(url, json=payload, timeout=10)

        if response.status_code in [429, 500, 502, 503, 504]:
            raise self.retry(exc=Exception(f'Telegram server error: {response.text}'))

        response.raise_for_status()
        return f'Повідомлення успішно надіслано у чат {chat_id}'

    except requests.RequestException as exc:
        error_message = exc.response.text if exc.response else str(exc)
        print(f"Telegram API Error: {error_message}")
        raise self.retry(exc=exc)


@shared_task(name='newsletter')
def send_newsletter_task(newsletter_id):
    try:
        newsletter = Newsletter.objects.get(id=newsletter_id)
    except Newsletter.DoesNotExist:
        return f'Розсилку з ID {newsletter_id} не знайдено.'

    newsletter.status = Newsletter.Status.SENDING
    newsletter.save(update_fields=['status'])

    image_url = None
    if newsletter.image:
        try:
            url = newsletter.image.url
            if url.startswith('http'):
                image_url = url
            else:
                image_url = f"{settings.BASE_URL}{url}"
        except Exception:
            image_url = None

    total_recipients = 0

    if newsletter.channel in [Newsletter.Channel.EMAIL, Newsletter.Channel.BOTH]:
        email_subscribers = User.objects.filter(
            is_active=True, is_subscribed_to_newsletter=True, email__isnull=False
        ).values_list('email', flat=True)

        for email in email_subscribers:
            if email:
                total_recipients += 1
                send_email_task.delay(email, newsletter.title, newsletter.body, image_url)

    if newsletter.channel in [Newsletter.Channel.TELEGRAM, Newsletter.Channel.BOTH]:
        tg_subscribers = User.objects.filter(
            is_active=True,
            is_subscribed_to_newsletter=True,
            telegram_chat_id__isnull=False,
        ).values_list('telegram_chat_id', flat=True)

        for chat_id in tg_subscribers:
            if chat_id:
                total_recipients += 1
                send_telegram_message_task.delay(
                    chat_id=chat_id,
                    message=f'<b>{newsletter.title}</b>\n\n{newsletter.body}',
                    image_url=image_url,
                )

    newsletter.status = Newsletter.Status.SENT
    newsletter.sent_at = timezone.now()
    newsletter.total_recipients = total_recipients
    newsletter.save(update_fields=['status', 'sent_at', 'total_recipients'])

    return f'Розсилка #{newsletter_id} успішно додана у чергу. Очікується відправка {total_recipients} повідомлень.'
