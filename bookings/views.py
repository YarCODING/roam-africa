import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db import transaction
from tours.models import Tour, TourDate
from .forms import BookingForm
from .models import Booking

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout_view(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, tour=tour)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user

            try:
                with transaction.atomic():
                    tour_date = TourDate.objects.select_for_update().get(pk=booking.tour_date.id)

                    if hasattr(tour_date, 'available_seats'):
                        if tour_date.available_seats < booking.persons_count:
                            messages.error(request, "На жаль, на цю дату залишилося менше місць, ніж ви вказали.")
                            return render(request, 'bookings/checkout.html', {'form': form, 'tour': tour})
                        
                        if tour_date.available_seats == 0:
                            tour_date.status = 'sold_out'
                        tour_date.save()

                    booking.save()
                    messages.success(request, f"Бронювання #{booking.id} успішно створено!")
                    return redirect('success', booking_id=booking.id)

            except TourDate.DoesNotExist:
                messages.error(request, "Помилка вибору даты тура.")
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        selected_date_id = request.GET.get('tour_date')
        initial_data = {
            'customer_name': request.user.name,
            'customer_email': request.user.email,
            'persons_count': 1,
        }
        if selected_date_id:
            initial_data['tour_date'] = selected_date_id

        form = BookingForm(initial=initial_data, tour=tour)

    return render(request, 'bookings/checkout.html', {
        'tour': tour,
        'form': form
    })

@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    return render(request, 'bookings/success.html', {'booking': booking})


@login_required
def bookings_list(request):
    bookings = Booking.objects.filter(customer=request.user).order_by('-status', '-created_at')
    return render(request, 'bookings/bookings_list.html', {'bookings':bookings})

@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        if booking.status in ['new', 'confirmed']:
            booking.status = 'canceled'
            booking.save()
    return redirect('bookings_list')

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})



@login_required
def create_stripe_checkout_session(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if booking.status != Booking.Status.CONFIRMED:
        return redirect('bookings_list')

    user = request.user
    
    session_kwargs = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': booking.tour_date.tour.title,
                    'description': f"Заїзд: {booking.tour_date.start_date.strftime('%d.%m.%Y')} — {booking.tour_date.end_date.strftime('%d.%m.%Y')} ({booking.persons_count} осіб)",
                },
                'unit_amount': int(booking.total_price * 100),
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

    if getattr(user, 'stripe_customer_id', None):
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
                    booking.status = Booking.Status.PAID
                    booking.save()

                    tour_date = booking.tour_date
                    tour_date.available_seats = max(0, tour_date.available_seats - booking.persons_count)
                    tour_date.save()
            except (Booking.DoesNotExist, ValueError):
                pass

        if user_id and stripe_customer_id:
            try:
                user = User.objects.get(id=int(user_id))
                if not getattr(user, 'stripe_customer_id', None):
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