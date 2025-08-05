import oscar.apps.payment.apps as apps


class PaymentConfig(apps.PaymentConfig):
    name = 'apps.payment'
    
    def ready(self):
        from .processor import PaystackPaymentDetailsView
        self.payment_details_view = PaystackPaymentDetailsView