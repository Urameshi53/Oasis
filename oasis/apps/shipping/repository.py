# your_project/shipping/repository.py
from oscar.apps.shipping import repository, methods
from . import methods as shipping_methods


class Repository(repository.Repository):
    def get_available_shipping_methods(self, basket, user=None, shipping_addr=None, request=None, **kwargs):
        """
        Return a list containing only the fixed price shipping method.
        """
        if basket.total_incl_tax >= 100:
            m =  [shipping_methods.FixedPriceShipping()]
        else:
            m =  [methods.Free()]
        return m

    def get_default_shipping_method(self, basket, user=None, shipping_addr=None, request=None, **kwargs):
        """
        Return the fixed price shipping method as the default.
        """
        if basket.total_incl_tax >= 100:
            return shipping_methods.FixedPriceShipping()
        else:
            return methods.Free()