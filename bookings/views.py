import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from allauth.account.decorators import verified_email_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db import transaction
from tours.models import Tour, TourDate, TourReview
from .forms import BookingForm
from .models import Booking, PromoCode
from .pdf_utils import generate_booking_ticket_pdf
from decimal import Decimal
from django.utils import timezone
from djmoney.money import Money
from .services import change_booking_status

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
@verified_email_required
def checkout_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    data = request.POST if request.method == 'POST' else request.GET
    
    selected_date_id = data.get('tour_date')
    persons_count = int(data.get('persons_count', 1))
    promo_code_str = data.get('promo_code', '').strip()
    
    tour_date = None
    price_per_person = None
    base_total = Decimal('0.00')
    loyalty_discount = Decimal('0.00')
    promo_discount = Decimal('0.00')
    total_price = Decimal('0.00')
    promo_success = None
    promo_error = None
    total_discount_percent = Decimal('0.00')

    if selected_date_id:
        try:
            tour_date = TourDate.objects.get(pk=selected_date_id, tour=tour)
            price_per_person = tour_date.price
            base_total = tour_date.price.amount * persons_count
            currency = tour_date.price.currency

            loyalty_percent = Decimal('0.00')
            if request.user.loyalty_tier:
                loyalty_percent = request.user.loyalty_tier.discount_percent
                loyalty_discount = (base_total * loyalty_percent) / Decimal('100.00')

            price_after_loyalty = base_total - loyalty_discount

            promo_percent = Decimal('0.00')
            if promo_code_str:
                now = timezone.now()
                try:
                    promo = PromoCode.objects.get(
                        code=promo_code_str,
                        valid_from__lte=now,
                        valid_to__gte=now
                    )
                    if promo.times_used < promo.usage_limit and base_total >= promo.min_order_amount:
                        valid_promo = promo
                        if promo.discount_type == 'percent':
                            promo_percent = promo.discount_value
                            promo_discount = (price_after_loyalty * promo_percent) / Decimal('100.00')
                            promo_success = f"Промокод застосовано: -{promo_percent}%"
                        else:
                            promo_discount = min(promo.discount_value, price_after_loyalty)
                            promo_success = f"Знижка -{promo.discount_value}"
                    else:
                        promo_error = "Промокод вичерпано або мінімальна сума не досягнута"
                except PromoCode.DoesNotExist:
                    promo_error = "Невірний або прострочений промокод"

            total_discount_percent = loyalty_percent + promo_percent
            calculated_total = base_total - loyalty_discount - promo_discount
            
            total_price = Money(max(calculated_total, Decimal('0.00')), currency)
            price_per_person = Money(tour_date.price.amount, currency)

        except TourDate.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = BookingForm(request.POST, tour=tour)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user

            selected_date_id = request.POST.get('tour_date') 

            try:
                with transaction.atomic():
                    tour_date_obj = TourDate.objects.select_for_update().get(pk=selected_date_id, tour=tour)

                    if tour_date_obj.available_seats:
                        if tour_date_obj.available_seats < booking.persons_count:
                            messages.error(request, "На жаль, на цю дату залишилося менше місць, ніж ви вказали.")
                            return render(request, 'bookings/checkout.html', {'form': form, 'tour': tour})

                        tour_date_obj.available_seats -= booking.persons_count
                        if tour_date_obj.available_seats == 0:
                            tour_date_obj.status = 'sold_out'
                        tour_date_obj.save()

                    booking.tour_date = tour_date_obj
                    
                    currency = tour_date_obj.price.currency
                    base_price_value = tour_date_obj.price.amount * booking.persons_count
                    
                    booking.original_price = Money(base_price_value, currency)
                    
                    loyalty_amount = Decimal('0.00')
                    if request.user.loyalty_tier:
                        percent = request.user.loyalty_tier.discount_percent
                        loyalty_amount = (Decimal(str(base_price_value)) * percent) / Decimal('100.00')
                    booking.loyalty_discount_amount = Money(loyalty_amount, currency)

                    promo_code_str = request.POST.get('promo_code', '').strip()
                    promo_discount_amount = Decimal('0.00')
                    
                    if promo_code_str:
                        now = timezone.now()
                        try:
                            promo = PromoCode.objects.get(
                                code=promo_code_str,
                                valid_from__lte=now,
                                valid_to__gte=now
                            )
                            price_after_loyalty = Decimal(str(base_price_value)) - loyalty_amount
                            
                            if promo.times_used < promo.usage_limit and Decimal(str(base_price_value)) >= promo.min_order_amount:
                                booking.promo_code = promo
                                if promo.discount_type == 'percent':
                                    promo_discount_amount = (price_after_loyalty * promo.discount_value) / Decimal('100.00')
                                else:
                                    promo_discount_amount = min(promo.discount_value, price_after_loyalty)
                                
                                promo.times_used += 1
                                promo.save()
                            else:
                                messages.warning(request, "Промокод не був застосований через обмеження суми або ліміту.")
                        except PromoCode.DoesNotExist:
                            pass

                    booking.promo_discount_amount = Money(promo_discount_amount, currency)
                    
                    final_amount = base_price_value - loyalty_amount - promo_discount_amount
                    booking.total_price = Money(final_amount, currency)

                    booking.save()

                    messages.success(request, f"Бронювання #{booking.id} успішно створено!")
                    return redirect('success', booking_id=booking.id)

            except TourDate.DoesNotExist:
                messages.error(request, "Помилка вибору дати туру.")
                return render(request, 'bookings/checkout.html', {'form': form, 'tour': tour})
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        initial_data = {
            'customer_name': getattr(request.user, 'name', request.user.get_full_name()),
            'customer_email': request.user.email,
            'persons_count': persons_count,
        }
        if selected_date_id:
            initial_data['tour_date'] = selected_date_id
        form = BookingForm(initial=initial_data, tour=tour)

    context = {
        'tour': tour,
        'form': form,
        'price_per_person': price_per_person,
        'total_price': total_price,
        'persons_count': persons_count,
        'promo_success': promo_success,
        'promo_error': promo_error,
        'applied_promo_code': promo_code_str,
        'total_discount_percent': total_discount_percent,
    }

    if request.headers.get('HX-Request') or getattr(request, 'htmx', False):
        return render(request, 'bookings/partials/checkout_totals.html', context)

    return render(request, 'bookings/checkout.html', context)

@login_required
@verified_email_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    return render(request, 'bookings/success.html', {'booking': booking})


@login_required
@verified_email_required
def bookings_list(request):
    bookings = Booking.objects.filter(customer=request.user)\
        .select_related('tour_date__tour')\
        .order_by('-status', '-created_at')

    reviewed_tour_ids = set(
        TourReview.objects.filter(user=request.user)
        .values_list('tour_id', flat=True)
    )

    for booking in bookings:
        tour = booking.tour_date.tour
        booking.has_review = tour.id in reviewed_tour_ids if tour else False

    context = {
        'bookings': bookings,
    }
    return render(request, 'bookings/bookings_list.html', context)

@login_required
@verified_email_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        if booking.status in ['new', 'confirmed']:
            booking.status = 'canceled'
            booking.save()
    return redirect('bookings_list')

@login_required
@verified_email_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})



@login_required
@verified_email_required
def create_stripe_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if booking.status != Booking.Status.CONFIRMED:
        return redirect('bookings_list')

    user = request.user
    
    session_kwargs = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'product_data': {
                    'name': booking.tour_date.tour.title,
                    'description': f"Заїзд: {booking.tour_date.start_date.strftime('%d.%m.%Y')} — {booking.tour_date.end_date.strftime('%d.%m.%Y')} ({booking.persons_count} осіб)",
                },
                'unit_amount': int(booking.total_price.amount * 100),
                'currency': str(booking.total_price.currency.code).lower(),
            },
            'quantity': 1,
        }],
        'mode': 'payment',
        'metadata': {
            'booking_id': booking.id,
            'user_id': user.id,
        },
        'success_url': request.build_absolute_uri(f'/bookings/payment/success/{booking.id}/'),
        'cancel_url': request.build_absolute_uri(f'/bookings/payment/cancel/{booking.id}/'),
        'payment_intent_data': {
            'setup_future_usage': 'on_session',
        },
    }

    if user.stripe_customer_id:
        session_kwargs['customer'] = user.stripe_customer_id
    else:
        session_kwargs['customer_email'] = user.email
        session_kwargs['customer_creation'] = 'always'

    session = stripe.checkout.Session.create(**session_kwargs)
    return redirect(session.url, code=303)



User = get_user_model()

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object'].to_dict()
        
        metadata = session.get('metadata', {})
        booking_id = metadata.get('booking_id')
        user_id = metadata.get('user_id')
        stripe_customer_id = session.get('customer')

        if booking_id:
            try:
                booking = Booking.objects.get(id=int(booking_id))
                if booking.status != Booking.Status.PAID:
                    change_booking_status(booking, Booking.Status.PAID)

                    tour_date = booking.tour_date
                    tour_date.save()
            except (Booking.DoesNotExist, ValueError):
                pass

        if user_id and stripe_customer_id:
            try:
                user = User.objects.get(id=int(user_id))
                if not user.stripe_customer_id:
                    user.stripe_customer_id = stripe_customer_id
                    user.save()
            except (User.DoesNotExist, ValueError):
                pass

    return HttpResponse(status=200)


@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    return render(request, 'bookings/payment_success.html', {'booking': booking})

@login_required
def payment_cancel(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    return render(request, 'bookings/payment_cancel.html', {'booking': booking})


@login_required
def download_booking_ticket(request, booking_id):
    if request.user.is_staff:
        booking = get_object_or_404(Booking, id=booking_id)
    else:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)

    pdf_data = generate_booking_ticket_pdf(booking)

    response = HttpResponse(pdf_data, content_type='application/pdf')
    filename = f"ticket_roam_africa_{booking.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def verify_booking_view(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            'tour_date__tour', 
            'tour_date__tour__country'
        ), 
        id=booking_id
    )
    
    return render(request, 'bookings/verify.html', {'booking': booking})