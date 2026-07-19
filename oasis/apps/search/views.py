# pylint: disable=E1101
from urllib.parse import quote
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

BrowseCategoryForm = get_class("search.forms", "BrowseCategoryForm")
CategoryForm = get_class("search.forms", "CategoryForm")
BaseSearchView = get_class("search.views.base", "BaseSearchView")
Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")

from .product_filters import filter_context


class CatalogueView(BaseSearchView):
    """
    Browse all products in the catalogue.

    Products are filtered/sorted/paginated by our own ORM-based filter system
    (``apps.search.product_filters``), so we bypass haystack's search + pager
    entirely and render the template directly.
    """

    form_class = BrowseCategoryForm
    context_object_name = "products"
    template_name = "oscar/catalogue/browse.html"
    enforce_paths = True

    def get(self, request, *args, **kwargs):
        books_category = Category.objects.filter(name__iexact="Books").first()
        base = Product.objects.browsable().exclude(categories=books_category)
        context = filter_context(request, base)
        context["summary"] = _("All products")
        return render(request, self.template_name, context)


class ProductCategoryView(BaseSearchView):
    """
    Browse products in a given category
    """

    form_class = CategoryForm
    enforce_paths = True
    context_object_name = "products"
    template_name = "oscar/catalogue/category.html"

    def get(self, request, *args, **kwargs):
        # pylint: disable=W0201
        self.category = self.get_category()

        # Allow staff members so they can test layout etc.
        if not self.is_viewable(self.category, request):
            raise Http404()

        potential_redirect = self.redirect_if_necessary(request.path, self.category)
        if potential_redirect is not None:
            return potential_redirect

        base = Product.objects.browsable().filter(categories=self.category)
        context = filter_context(request, base)
        context["category"] = self.category
        return render(request, self.template_name, context)

    def is_viewable(self, category, request):
        return category.is_public or request.user.is_staff

    def redirect_if_necessary(self, current_path, category):
        if self.enforce_paths:
            # Categories are fetched by primary key to allow slug changes.
            # If the slug has changed, issue a redirect.
            expected_path = category.get_absolute_url()
            if expected_path != quote(current_path):
                return HttpResponsePermanentRedirect(expected_path)

    def get_category(self):
        return get_object_or_404(Category, pk=self.kwargs["pk"])
