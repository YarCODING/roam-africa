from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_form_class(self):
        from users.forms import CustomSignupForm
        return CustomSignupForm

    def instantiate_form(self, form_class, *args, **kwargs):
        if 'request' not in kwargs:
            kwargs['request'] = self.request
        return form_class(*args, **kwargs)