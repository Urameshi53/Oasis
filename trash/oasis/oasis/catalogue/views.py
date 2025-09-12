from oscar.core.loading import get_model
from django.views.generic import ListView

Product = get_model('catalogue', 'Product')

class ProductListView(ListView):
    model = Product
    template_name = 'your_app/product_list.html'  # Adjust path as needed
    context_object_name = 'products'  # Name of the variable in the template