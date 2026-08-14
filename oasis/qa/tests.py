from django.test import TestCase
from django.urls import reverse

from qa.models import ProductAnswer, ProductQuestion
from oasis.testutils import make_seller_product, make_user


class ProductQATests(TestCase):
    def setUp(self):
        self.seller = make_user("seller")
        self.buyer = make_user("buyer")
        self.product = make_seller_product(self.seller, partner_name="Shop")

    def test_ask_creates_question(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("qa:ask", args=[self.product.pk]), {"body": "In stock?"})
        self.assertEqual(self.product.questions.count(), 1)

    def test_seller_answer_is_flagged(self):
        q = ProductQuestion.objects.create(product=self.product, user=self.buyer, body="Q?")
        self.client.force_login(self.seller)
        self.client.post(reverse("qa:answer", args=[q.pk]), {"body": "Yes, in stock."})
        ans = q.answers.get()
        self.assertTrue(ans.is_seller)

    def test_community_answer_not_flagged_and_sorts_after_seller(self):
        q = ProductQuestion.objects.create(product=self.product, user=self.buyer, body="Q?")
        other = make_user("shopper")
        self.client.force_login(other)
        self.client.post(reverse("qa:answer", args=[q.pk]), {"body": "I think so."})
        self.client.force_login(self.seller)
        self.client.post(reverse("qa:answer", args=[q.pk]), {"body": "Confirmed."})
        # ordering: seller answer first
        answers = list(q.answers.all())
        self.assertTrue(answers[0].is_seller)
        self.assertFalse(answers[1].is_seller)

    def test_anonymous_cannot_ask(self):
        resp = self.client.post(reverse("qa:ask", args=[self.product.pk]), {"body": "hi"})
        self.assertEqual(resp.status_code, 302)  # redirected to login wall
        self.assertEqual(self.product.questions.count(), 0)
