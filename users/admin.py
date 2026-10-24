from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from allauth.account.admin import EmailAddressAdmin as BaseEmailAddressAdmin

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin
from .models import LoyaltyTier

User = get_user_model()

admin.site.unregister(Group)

def is_senior_staff(user):
    return user.is_superuser or user.groups.filter(name='Вищі менеджери').exists()

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ("username", "email", "trips_count", "loyalty_tier", "is_staff")
    
    list_filter = BaseUserAdmin.list_filter + ("is_subscribed_to_newsletter", "loyalty_tier")

    fieldsets = (
        (
            "Інформація про профіль", 
            {
                'fields': (
                    'displayname', 
                    'image',  
                    'info', 
                    'trips_count', 
                    'loyalty_tier', 
                    'stripe_customer_id', 
                    'telegram_chat_id', 
                    'is_subscribed_to_newsletter'
                )
            }
        ),
    ) + BaseUserAdmin.fieldsets

    search_fields = ("username", "email", "phone", "first_name", "last_name")

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


    def has_change_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser:
            disabled_fields = ['user_permissions']
            for field in disabled_fields:
                if field in form.base_fields:
                    form.base_fields[field].disabled = True
                    
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if not request.user.is_superuser:
            new_fieldsets = []
            for name, field_options in fieldsets:
                fields = field_options.get('fields', ())
                
                filtered_fields = tuple(
                    f for f in fields if f not in ('user_permissions', 'stripe_customer_id', 'telegram_chat_id', 'password')
                )
                
                if filtered_fields:
                    new_options = dict(field_options)
                    new_options['fields'] = filtered_fields
                    new_fieldsets.append((name, new_options))
            
            return tuple(new_fieldsets)
            
        return fieldsets


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

admin.site.unregister(EmailAddress)

@admin.register(EmailAddress)
class EmailAddressAdmin(BaseEmailAddressAdmin, ModelAdmin):
    list_filter = ("verified", "primary")
    search_fields = ("email", "user__username", "user__email")


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(ModelAdmin):
    list_display = ("name", "min_trips", "discount_percent")
    search_fields = ("name",)
    ordering = ("min_trips",)