from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Country, Tour, TourReview
from .forms import VisaCheckForm, TourReviewForm
from .services import get_visa_requirement
from bookings.models import Booking
from .forms import TourReviewForm

def country_view(request, slug):
    country = get_object_or_404(Country, slug=slug)
    if request.user.is_staff:
        tours = country.tours.all()
    else:
        tours = country.tours.published()

    return render(request, 'tours/country_detail.html', {
        'country': country,
        'tours': tours,
    })


def tour_view(request, slug):
    queryset = Tour.objects.all() if request.user.is_staff else Tour.objects.published()

    tour = get_object_or_404(
        queryset.select_related('country').prefetch_related('images', 'dates', 'itinerary_days', 'inclusions', 'reviews__user'),
        slug=slug
    )

    reviews = tour.reviews.order_by('-created_at')
    review_stats = reviews.aggregate(
        avg_total=Avg('rating_total'),
        avg_guide=Avg('rating_guide'),
        avg_program=Avg('rating_program'),
        avg_logistic=Avg('rating_logistic'),
        total_count=Count('id')
    )

    avg_total_rounded = round(review_stats['avg_total']) if review_stats['avg_total'] else 0

    has_completed = False
    already_reviewed = False

    if request.user.is_authenticated:
        has_completed = Booking.objects.filter(
            customer=request.user, 
            tour_date__tour=tour, 
            status='completed'
        ).exists()

        already_reviewed = TourReview.objects.filter(user=request.user, tour=tour).exists()

    form = VisaCheckForm(request.GET or None)
    visa_info = None

    if form.is_valid():
        user_citizenship = form.cleaned_data['citizenship']
        destination_code = tour.country.code
        
        visa_info = get_visa_requirement(user_citizenship, destination_code)

    context = {
        'tour': tour,
        'reviews': reviews,
        'review_stats': review_stats,
        'avg_total_rounded': avg_total_rounded,
        'form': form,
        'visa_info': visa_info,
        'has_completed': has_completed,
        'already_reviewed': already_reviewed,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'tours/includes/visa_result.html', context)

    return render(request, 'tours/tour_detail.html', context)


def tour_list(request):
    tours = Tour.objects.filter(is_active=True).select_related('country')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tours = tours.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    country_id = request.GET.get('country')
    if country_id:
        tours = tours.filter(country_id=country_id)

    difficulty = request.GET.get('difficulty')
    if difficulty in dict(Tour.Difficulty.choices):
        tours = tours.filter(difficulty=difficulty)

    sort_by = request.GET.get('sort', '-created_at')
    allowed_sorts = {
        'price_asc': 'price_from',
        'price_desc': '-price_from',
        'duration_asc': 'duration_days',
        'duration_desc': '-duration_days',
        'newest': '-created_at',
    }
    tours = tours.order_by(allowed_sorts.get(sort_by, '-created_at'))

    paginator = Paginator(tours, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'countries': Country.objects.all(),
        'difficulties': Tour.Difficulty.choices,
        'selected_country': country_id,
        'selected_difficulty': difficulty,
        'search_query': search_query,
        'sort_by': sort_by,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'tours/includes/tour_grid.html', context)

    return render(request, 'tours/tour_list.html', context)

def reviews_page(request):
    reviews = TourReview.objects.filter(rating_total__gte=4)\
                               .select_related('user', 'tour')\
                               .order_by('-created_at')

    stats = TourReview.objects.aggregate(
        avg_total=Avg('rating_total'),
        avg_guide=Avg('rating_guide'),
        avg_program=Avg('rating_program'),
        avg_logistic=Avg('rating_logistic'),
        total_count=Count('id')
    )

    return render(request, 'tours/reviews.html', {
        'reviews': reviews,
        'stats': stats,
    })

@login_required
def leave_review_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    user = request.user

    has_completed = Booking.objects.filter(
        customer=request.user, 
        tour_date__tour=tour, 
        status='completed'
    ).exists()
    
    if not has_completed:
        return HttpResponseForbidden("Ви можете залишити відгук лише після завершення цього туру.")

    already_reviewed = TourReview.objects.filter(user=user, tour=tour).exists()
    if already_reviewed:
        messages.error(request, "Ви вже залишили відгук про цей тур.")
        return redirect('tour_detail', slug=tour.slug)

    if request.method == 'POST':
        form = TourReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = user
            review.tour = tour
            review.save()
            
            messages.success(request, "Дякуємо! Ваш відгук успішно опубліковано.")
            return redirect('tour_detail', slug=tour.slug)
    else:
        form = TourReviewForm()

    context = {
        'form': form,
        'tour': tour,
    }
    return render(request, 'tours/leave_review.html', context)
