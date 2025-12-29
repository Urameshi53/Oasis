from oscar.apps.catalogue.models import Product, ProductImage
from rest_framework import serializers


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["original"]


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    price = serializers.SerializerMethodField()  # Add price field
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['title', 'upc', 'price', 'primary_image']  # Include price

    def get_price(self, obj):
        stockrecord = obj.stockrecords.first()
        if stockrecord and stockrecord.price is not None:
            return str(stockrecord.price)
        return None
    
    def get_primary_image(self, obj):
        image = obj.primary_image()
        if not image:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(image.original.url)

        return image.original.url

