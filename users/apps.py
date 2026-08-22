from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'
    verbose_name = 'Користувачі'

    def ready(self):
        import users.signals