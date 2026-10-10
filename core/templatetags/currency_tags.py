from django import template
from djmoney.contrib.exchange.models import convert_money

register = template.Library()

def convert_to_user_currency(value, request):
    if not value:
        return ""
    
    target_currency = request.session.get('currency', 'EUR')
    
    if str(value.currency) == target_currency:
        return value

    try:
        return convert_money(value, target_currency)
    except Exception:
        return value

register.filter("convert", convert_to_user_currency)