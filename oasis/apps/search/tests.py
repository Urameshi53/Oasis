from django.test import TestCase

from apps.search.product_filters import build_search_queryset
from oasis.testutils import make_product


class SearchRelevanceTests(TestCase):
    def setUp(self):
        # Title match should outrank a description-only match.
        self.exact = make_product(title="Blue Notebook")
        self.desc = make_product(title="Random Item")
        self.desc.description = "A blue cover notebook accessory"
        self.desc.save()
        self.laptop = make_product(title="Gaming Laptop")
        self.other = make_product(title="Office Chair")

    def test_title_match_ranks_first(self):
        results = list(build_search_queryset("notebook"))
        self.assertEqual(results[0], self.exact)
        self.assertIn(self.desc, results)

    def test_multi_word_requires_all_terms(self):
        results = list(build_search_queryset("gaming laptop"))
        self.assertIn(self.laptop, results)
        self.assertNotIn(self.other, results)

    def test_fallback_to_any_term_when_no_full_match(self):
        # "laptop zzzznomatch" -> no product has both, falls back to 'laptop'
        results = list(build_search_queryset("laptop zzzznomatch"))
        self.assertIn(self.laptop, results)

    def test_no_terms_returns_empty(self):
        self.assertEqual(list(build_search_queryset("")), [])
