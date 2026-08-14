"""
Seed example product questions & answers so the Q&A section has data.

    python manage.py seed_qa           # add Q&A to seeded products
    python manage.py seed_qa --all     # cover every product
    python manage.py seed_qa --wipe    # delete all Q&A first

Run with PYTHONIOENCODING=utf-8 on Windows.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")

QUESTIONS = [
    "Is this available in other colours?",
    "How long does delivery usually take?",
    "Does it come with a warranty?",
    "Is this the original brand or a copy?",
    "What are the dimensions?",
    "Can I pay on delivery?",
    "Is it in stock right now?",
    "Does the price include delivery?",
]
ANSWERS = [
    "Yes, I bought one recently and it works great.",
    "Delivery took about two days for me.",
    "Mine came well packaged and as described.",
    "Yes, it's the genuine product.",
    "I asked the seller and they confirmed it's in stock.",
    "Works perfectly, would recommend.",
]


class Command(BaseCommand):
    help = "Seed example product questions and answers."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--seed", type=int, default=5)

    @transaction.atomic
    def handle(self, *args, **options):
        from qa.models import ProductAnswer, ProductQuestion

        rng = random.Random(options["seed"])

        if options["wipe"]:
            nq = ProductQuestion.objects.count()
            ProductQuestion.objects.all().delete()
            self.stdout.write(self.style.WARNING("Deleted %d question(s)." % nq))

        from django.contrib.auth import get_user_model

        users = list(get_user_model().objects.filter(is_active=True))
        if not users:
            self.stderr.write("No users to author Q&A.")
            return

        products = Product.objects.browsable()
        if not options["all"]:
            products = products.filter(upc__startswith="OASIS-")

        nq = na = 0
        for product in products:
            if product.questions.exists():
                continue
            for _ in range(rng.randint(0, 3)):
                asker = rng.choice(users)
                q = ProductQuestion.objects.create(
                    product=product, user=asker, body=rng.choice(QUESTIONS)
                )
                nq += 1
                for _ in range(rng.randint(0, 2)):
                    ans = rng.choice([u for u in users if u.id != asker.id] or users)
                    ProductAnswer.objects.create(
                        question=q, user=ans, body=rng.choice(ANSWERS)
                    )
                    na += 1

        self.stdout.write(
            self.style.SUCCESS("Seeded %d question(s) and %d answer(s)." % (nq, na))
        )
