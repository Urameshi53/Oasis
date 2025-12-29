from django.conf import settings

def modern_settings(request):
    return {
        'site_name': getattr(settings, 'OSCAR_SHOP_NAME', 'Modern Store'),
        'site_tagline': getattr(settings, 'OSCAR_SHOP_TAGLINE', 'Premium E-commerce'),
        'current_year': '2024',
        'featured_categories': [
            {'name': 'Electronics', 'icon': 'bi-phone', 'color': 'primary'},
            {'name': 'Fashion', 'icon': 'bi-tshirt', 'color': 'danger'},
            {'name': 'Home & Garden', 'icon': 'bi-house', 'color': 'success'},
            {'name': 'Sports', 'icon': 'bi-trophy', 'color': 'warning'},
            {'name': 'Books', 'icon': 'bi-book', 'color': 'info'},
            {'name': 'Beauty', 'icon': 'bi-flower1', 'color': 'secondary'},
        ]
    }