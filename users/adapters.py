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

        subject = self.render_mail(template_prefix, email, ctx, subject_only=True)
        subject = ''.join(subject.splitlines())

        message = self.render_mail(template_prefix, email, ctx, prefix='txt')
        html_message = self.render_mail(
            template_prefix, email, ctx, prefix='html'
        )

        send_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=[email],
            html_message=html_message if html_message else None,
        )