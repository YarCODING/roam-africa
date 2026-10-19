from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import *

from .tasks import send_newsletter_task

@admin.register(Newsletter)
class NewsletterAdmin(ModelAdmin):
    list_display = ("title", "channel", "author", "created_at")
    search_fields = ("title", "body")
    list_filter = ("author", )
    exclude = ('author',)
    readonly_fields = ('sent_at', 'total_recipients', 'success_count', 'fail_count', 'created_at', 'updated_at')

    actions = ['trigger_newsletter_send']

    @admin.action(description='Надіслати')
    def trigger_newsletter_send(self, request, queryset):
        for newsletter in queryset:
            send_newsletter_task.delay(newsletter.id)
        
        self.message_user(request, f"Надіслано розсилок: {queryset.count()}")
        

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)