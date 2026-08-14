"""
Seed the Oscar catalogue with example products across every storefront
category, each with a partner + priced stock record so it is browsable and
buyable. Idempotent: re-running updates price/stock instead of duplicating
(products are keyed by UPC).

    python manage.py seed_products          # create/update the sample catalogue
    python manage.py seed_products --wipe   # first delete previously seeded rows

Run with PYTHONIOENCODING=utf-8 on Windows so the summary can print cleanly.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")
ProductClass = get_model("catalogue", "ProductClass")
ProductCategory = get_model("catalogue", "ProductCategory")
Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")

CURRENCY = "GHS"
SEED_PREFIX = "OASIS-"  # UPC prefix marks a row as seeded (used by --wipe)

# Partner (vendor) per broad department, so the "Sold by" line varies nicely.
PARTNERS = {
    "books": "Aki Ola Books",
    "fashion": "Campus Threads",
    "tech": "Lancetech Technologies",
    "food": "Owahene Foods",
    "grocery": "Continental Market",
    "home": "Calabash",
}

# Each entry: (breadcrumb, product_class, partner_key, title, price, stock, description)
PRODUCTS = [
    # ---------------- Books ----------------
    ("Books > Business Books", "Book", "books", "The Lean Startup", 85, 40,
     "A practical guide to building companies with continuous innovation."),
    ("Books > Business Books", "Book", "books", "Rich Dad Poor Dad", 70, 55,
     "Robert Kiyosaki's classic on financial literacy and investing."),
    ("Books > Christian Books", "Book", "books", "The Purpose Driven Life", 60, 35,
     "Rick Warren's 40-day spiritual journey to discovering your purpose."),
    ("Books > Marriage Books", "Book", "books", "The Five Love Languages", 65, 30,
     "How to express heartfelt commitment to your partner."),
    ("Books > Trading", "Book", "books", "Trading in the Zone", 120, 20,
     "Master the mental game of trading and consistent execution."),
    ("Books", "Book", "books", "Things Fall Apart", 55, 48,
     "Chinua Achebe's landmark novel of pre-colonial Nigeria."),

    # ---------------- Fashion ----------------
    ("Fashion > Shoes", "Shoe", "fashion", "Classic White Sneakers", 220, 25,
     "Everyday low-top sneakers in clean white leather-look finish."),
    ("Fashion > Shoes", "Shoe", "fashion", "Suede Desert Boots", 320, 15,
     "Comfortable crepe-sole boots that pair with anything."),
    ("Fashion > Shirts", "Shirt", "fashion", "Oxford Button-Down Shirt", 140, 40,
     "Breathable cotton oxford shirt for lectures or a night out."),
    ("Fashion > Trousers", "Trouser", "fashion", "Slim-Fit Chinos", 160, 35,
     "Stretch chinos with a tailored slim fit in stone beige."),
    ("Fashion > Suits", "Shirt", "fashion", "Two-Piece Slim Suit", 850, 10,
     "Sharp single-breasted suit for interviews and ceremonies."),
    ("Fashion", "Bag", "fashion", "Canvas Backpack", 180, 30,
     "Water-resistant campus backpack with a padded laptop sleeve."),

    # ---------------- Laptops / Electronics ----------------
    ("Laptops > Gaming Laptop", "Laptop", "tech", "Predator Nitro 15 Gaming Laptop", 9800, 8,
     "RTX graphics, 16GB RAM and a 144Hz display for serious gaming."),
    ("Laptops > Office Laptop", "Laptop", "tech", "ProBook 14 Business Laptop", 6500, 12,
     "Lightweight all-day battery laptop for study and office work."),
    ("Laptops", "Laptop", "tech", "UltraSlim Student Notebook", 4200, 20,
     "Affordable 14-inch notebook for browsing, notes and streaming."),
    ("Electronics", "Airpods", "tech", "Wireless Earbuds Pro", 450, 45,
     "Noise-cancelling wireless earbuds with a charging case."),
    ("Electronics", "Iron", "tech", "Steam Iron 2000W", 260, 25,
     "Fast-heating steam iron with anti-drip and self-clean."),
    ("Electronics", "Airpods", "tech", "Bluetooth Party Speaker", 780, 14,
     "Portable speaker with deep bass and 12-hour playtime."),

    # ---------------- Fast Food ----------------
    ("Fast Food > Jollof", "Fast Food", "food", "Party Jollof with Chicken", 45, 100,
     "Smoky Ghanaian jollof rice served with grilled chicken."),
    ("Fast Food > Waakye", "Fast Food", "food", "Waakye Special", 40, 100,
     "Rice and beans with spaghetti, gari, egg and shito."),
    ("Fast Food > Shawarma", "Fast Food", "food", "Chicken Shawarma", 35, 100,
     "Loaded chicken shawarma wrap with garlic sauce."),
    ("Fast Food > Fried Rice", "Fast Food", "food", "Fried Rice & Chicken", 50, 100,
     "Vegetable fried rice with a quarter grilled chicken."),
    ("Fast Food > Fried Yam", "Fast Food", "food", "Fried Yam & Pepper", 25, 100,
     "Golden fried yam served with spicy pepper sauce."),
    ("Fast Food > Sausage", "Fast Food", "food", "Grilled Sausage Combo", 30, 100,
     "Two grilled sausages with fries and ketchup."),

    # ---------------- Food ----------------
    ("Food", "Bread", "grocery", "Sugar Bread Loaf", 18, 60,
     "Soft freshly-baked sugar bread, perfect for breakfast."),
    ("Food", "Eggs", "grocery", "Crate of Eggs (30)", 55, 40,
     "A full crate of farm-fresh eggs."),
    ("Food", "Food", "grocery", "Groundnut Paste 500g", 28, 50,
     "Pure roasted groundnut paste for soups and snacks."),
    ("Food", "Food", "grocery", "Local Honey 500ml", 90, 22,
     "Raw, unfiltered honey harvested locally."),

    # ---------------- Groceries ----------------
    ("Groceries > Rice", "Grocery", "grocery", "Perfumed Rice 5kg", 120, 40,
     "Long-grain aromatic rice in a resealable 5kg bag."),
    ("Groceries", "Grocery", "grocery", "Vegetable Cooking Oil 5L", 145, 30,
     "Cholesterol-free vegetable oil for everyday cooking."),
    ("Groceries", "Cream", "grocery", "Shea Body Cream 400ml", 48, 45,
     "Natural shea butter cream for smooth, hydrated skin."),
    ("Groceries", "Soap", "grocery", "Antibacterial Soap (Pack of 4)", 32, 70,
     "Family pack of gentle antibacterial bath soap."),
    ("Groceries", "Grocery", "grocery", "Milo Chocolate Drink 400g", 60, 50,
     "Energy chocolate malt drink refill pack."),

    # ---------------- Kitchen ----------------
    ("Kitchen", "Blender", "home", "2-in-1 Countertop Blender", 380, 18,
     "Powerful blender with grinder mill for smoothies and spices."),
    ("Kitchen", "Gas", "home", "6kg LPG Gas Cylinder (Full)", 520, 12,
     "Refilled 6kg cooking gas cylinder with safety valve."),
    ("Kitchen", "Blender", "home", "Non-Stick Cookware Set (5pc)", 640, 10,
     "Five-piece non-stick pots and pan set with glass lids."),
    ("Kitchen", "Iron", "home", "Electric Kettle 1.7L", 190, 26,
     "Cordless stainless-steel kettle with auto shut-off."),
]


class Command(BaseCommand):
    help = "Seed the catalogue with example products across all categories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete previously seeded products (UPC starting %s) first."
            % SEED_PREFIX,
        )

    def _get_partner(self, key):
        name = PARTNERS[key]
        partner, _ = Partner.objects.get_or_create(name=name)
        return partner

    def _get_product_class(self, name):
        pc = ProductClass.objects.filter(name=name).first()
        if pc is None:
            pc = ProductClass.objects.create(name=name)
        return pc

    @transaction.atomic
    def handle(self, *args, **options):
        if options["wipe"]:
            qs = Product.objects.filter(upc__startswith=SEED_PREFIX)
            n = qs.count()
            qs.delete()
            self.stdout.write(self.style.WARNING("Wiped %d seeded product(s)." % n))

        created, updated = 0, 0
        cat_cache = {}

        for i, (crumb, klass, pkey, title, price, stock, desc) in enumerate(PRODUCTS, 1):
            upc = "%s%04d" % (SEED_PREFIX, i)
            product_class = self._get_product_class(klass)

            product, was_created = Product.objects.get_or_create(
                upc=upc,
                defaults={
                    "title": title,
                    "description": desc,
                    "structure": Product.STANDALONE,
                    "product_class": product_class,
                    "is_public": True,
                },
            )
            if not was_created:
                product.title = title
                product.description = desc
                product.product_class = product_class
                product.is_public = True
                product.save()

            # Category (create the tree branch if missing) + link.
            if crumb not in cat_cache:
                cat_cache[crumb] = create_from_breadcrumbs(crumb)
            category = cat_cache[crumb]
            ProductCategory.objects.get_or_create(product=product, category=category)

            # Priced stock so the product is buyable.
            partner = self._get_partner(pkey)
            StockRecord.objects.update_or_create(
                product=product,
                partner=partner,
                defaults={
                    "partner_sku": upc,
                    "price_currency": CURRENCY,
                    "price": Decimal(str(price)),
                    "num_in_stock": stock,
                },
            )

            created += was_created
            updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete: %d created, %d updated (%d total example products)."
                % (created, updated, len(PRODUCTS))
            )
        )
