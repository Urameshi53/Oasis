from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from restaurant.models import Restaurant, Category, MenuItem, Addon

User = get_user_model()

# name -> description, [ (category, [ (item, price, desc, [ (addon, price) ]) ]) ]
DEMO = {
    "Campus Grill": {
        "description": "Flame-grilled burgers, wraps and loaded fries — a student favourite.",
        "address": "Block A, Student Union",
        "menu": {
            "Burgers": [
                ("Classic Beef Burger", "12.00", "Beef patty, lettuce, tomato, house sauce.",
                 [("Extra cheese", "2.00"), ("Bacon", "3.50")]),
                ("Crispy Chicken Burger", "13.50", "Buttermilk-fried chicken, slaw, mayo.",
                 [("Extra patty", "5.00")]),
            ],
            "Sides": [
                ("Loaded Fries", "8.00", "Fries topped with cheese sauce and spring onion.", []),
                ("Onion Rings", "5.50", "Golden, crispy battered onion rings.", []),
            ],
            "Drinks": [
                ("Soft Drink", "3.00", "Chilled can of your choice.", []),
            ],
        },
    },
    "Noodle Bar": {
        "description": "Fresh, fast Asian-inspired noodles and rice bowls.",
        "address": "Food Court, Level 1",
        "menu": {
            "Noodles": [
                ("Chicken Chow Mein", "14.00", "Stir-fried noodles, chicken, veg.",
                 [("Extra chicken", "4.00"), ("Fried egg", "2.00")]),
                ("Veg Singapore Noodles", "12.50", "Curried rice noodles with mixed veg.", []),
            ],
            "Rice Bowls": [
                ("Teriyaki Chicken Rice", "15.00", "Grilled chicken, teriyaki glaze, steamed rice.", []),
            ],
        },
    },
    "The Coffee Corner": {
        "description": "Coffee, pastries and quick bites between lectures.",
        "address": "Library Foyer",
        "menu": {
            "Hot Drinks": [
                ("Cappuccino", "4.50", "Double espresso with steamed milk.",
                 [("Extra shot", "1.50"), ("Oat milk", "1.00")]),
                ("Hot Chocolate", "4.00", "Rich chocolate topped with cream.", []),
            ],
            "Pastries": [
                ("Butter Croissant", "3.50", "Freshly baked, flaky croissant.", []),
                ("Blueberry Muffin", "3.80", "Packed with real blueberries.", []),
            ],
        },
    },
}


class Command(BaseCommand):
    help = "Seed the database with sample restaurants, menus and add-ons for development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--owner",
            default=None,
            help="Username of the user to own the demo restaurants. Defaults to the first superuser.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        owner = self._get_owner(options.get("owner"))
        if owner is None:
            self.stderr.write(self.style.ERROR(
                "No owner found. Create a superuser first, or pass --owner <username>."
            ))
            return

        created_count = 0
        for name, data in DEMO.items():
            restaurant, created = Restaurant.objects.get_or_create(
                name=name,
                defaults={
                    "owner": owner,
                    "description": data["description"],
                    "address": data["address"],
                    "is_active": True,
                },
            )
            if not created:
                self.stdout.write(f"{name} already exists — skipping.")
                continue

            created_count += 1
            for cat_name, items in data["menu"].items():
                category = Category.objects.create(restaurant=restaurant, name=cat_name)
                for item_name, price, desc, addons in items:
                    item = MenuItem.objects.create(
                        category=category,
                        name=item_name,
                        description=desc,
                        base_price=Decimal(price),
                        is_available=True,
                    )
                    for addon_name, addon_price in addons:
                        Addon.objects.create(
                            menu_item=item, name=addon_name, price=Decimal(addon_price)
                        )
            self.stdout.write(self.style.SUCCESS(f"Created {name}"))

        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_count} new restaurant(s) added (owner: {owner.get_username()})."
        ))

    def _get_owner(self, username):
        if username:
            return User.objects.filter(username=username).first()
        return (
            User.objects.filter(is_superuser=True).order_by("id").first()
            or User.objects.order_by("id").first()
        )
