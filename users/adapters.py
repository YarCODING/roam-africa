from allauth.account.adapter import DefaultAccountAdapter
from newsletter.tasks import send_email_task

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_form_class(self):
        from users.forms import CustomSignupForm
        return CustomSignupForm

    def instantiate_form(self, form_class, *args, **kwargs):
        if 'request' not in kwargs:
            kwargs['request'] = self.request
        return form_class(*args, **kwargs)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def send_mail(self, template_prefix, email, context):
        ctx = {
            'email': email,
            **context,
        }

        message_obj = super().render_mail(template_prefix, email, ctx)
        subject = message_obj.subject

        activate_url = context.get('activate_url', '')

        body = f"""
                <p>Дякуємо за реєстрацію! Для підтвердження вашої електронної пошти, будь ласка, перейдіть за посиланням:</p>
                <p style="margin: 20px 0;">
                    <a href="{activate_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Підтвердити пошту
                    </a>
                </p>
                <p>Якщо ви не створювали акаунт, просто проігноруйте цей лист.</p>
            """

        send_email_task.delay(
            email=email if isinstance(email, str) else email[0],
            title=subject,
            body=body,
        )