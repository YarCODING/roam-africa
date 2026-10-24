from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from .models import Article, Category


def blog_list_view(request):
    category_slug = request.GET.get("category")
    search_query = request.GET.get("q", "").strip()
    categories = Category.objects.all()
    articles = Article.objects.filter(is_published=True)

    if category_slug:
        articles = articles.filter(category__slug=category_slug)

    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )

    paginator = Paginator(articles, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": category_slug,
        "search_query": search_query,
    }

    if request.htmx:
        return render(request, "blog/partials/article_list_content.html", context)

    return render(request, "blog/blog_list.html", context)


def blog_detail_view(request, slug):
  article = get_object_or_404(Article, slug=slug, is_published=True)

  article.views_count += 1
  article.save(update_fields=["views_count"])

  related_articles = (
      Article.objects.filter(category=article.category, is_published=True)
      .exclude(id=article.id)
      .order_by("-created_at")[:3]
  )

  context = {
      "article": article,
      "related_articles": related_articles,
  }
  return render(request, "blog/blog_detail.html", context)