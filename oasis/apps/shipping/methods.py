# your_project/shipping/methods.py
from decimal import Decimal as D
from oscar.apps.shipping import methods
from oscar.core import prices

class FixedPriceShipping(methods.Base):
    code = 'fixed-price-shipping'
    name = 'Standard Fixed Rate'
    price_per_order = D('5.00')  # Example fixed price

    def calculate(self, basket):
        # The calculate method determines the shipping cost

        return prices.Price(
            currency=basket.currency,
            excl_tax=self.price_per_order,
            incl_tax=self.price_per_order  # Assuming no tax calculation here, or handle as needed
        )