# bookings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from tours.models import Tour, TourDate
from .forms import BookingForm
from .models import Booking

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
                        
                        tour_date.available_seats -= booking.persons_count
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
            'customer_name': request.user.get_full_name() or request.user.username,
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