"""
Generate clean, category-branded placeholder images for the seeded example
products (those with a UPC starting ``OASIS-``) — no external downloads.

    python manage.py seed_product_images           # add images where missing
    python manage.py seed_product_images --force    # regenerate all
    python manage.py seed_product_images --all       # also cover non-seeded products

Each image is an 800x800 PNG: a department-coloured gradient, an initials
monogram, a category chip and the wrapped product title. Run with
PYTHONIOENCODING=utf-8 on Windows.
"""

import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from oscar.core.loading import get_model
from PIL import Image, ImageDraw, ImageFont

Product = get_model("catalogue", "Product")
ProductImage = get_model("catalogue", "ProductImage")

SIZE = 800

# Two-stop vertical gradient per top-level category (top, bottom) RGB.
CATEGORY_COLORS = {
    "Books": ((37, 99, 235), (29, 78, 216)),          # blue
    "Fashion": ((219, 39, 119), (157, 23, 77)),        # pink/magenta
    "Laptops": ((15, 118, 110), (6, 78, 59)),          # teal/green
    "Electronics": ((79, 70, 229), (49, 46, 129)),     # indigo
    "Fast Food": ((234, 88, 12), (154, 52, 18)),       # orange
    "Food": ((202, 138, 4), (133, 77, 14)),            # amber
    "Groceries": ((22, 163, 74), (20, 83, 45)),        # green
    "Kitchen": ((100, 116, 139), (51, 65, 85)),        # slate
}
DEFAULT_COLORS = ((13, 77, 184), (8, 47, 115))  # brand blue


def _font(size, bold=True):
    candidates = (
        ["arialbd.ttf", "Arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(top, bottom):
    base = Image.new("RGB", (1, SIZE))
    for y in range(SIZE):
        t = y / (SIZE - 1)
        base.putpixel(
            (0, y),
            tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return base.resize((SIZE, SIZE))


def _initials(title):
    words = [w for w in title.split() if w[:1].isalnum()]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _wrap(draw, text, font, max_width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:4]


def _top_category(product):
    cat = product.categories.first()
    if cat is None:
        return None, DEFAULT_COLORS
    root_name = cat.full_name.split(">")[0].strip()
    return root_name, CATEGORY_COLORS.get(root_name, DEFAULT_COLORS)


def render_product_image(product):
    root_name, (top, bottom) = _top_category(product)
    img = _gradient(top, bottom)
    draw = ImageDraw.Draw(img, "RGBA")

    # Soft decorative circles.
    draw.ellipse((-120, -120, 260, 260), fill=(255, 255, 255, 22))
    draw.ellipse((SIZE - 180, SIZE - 320, SIZE + 220, SIZE + 120), fill=(0, 0, 0, 28))

    # Monogram badge.
    badge_r = 120
    cx, cy = SIZE // 2, 300
    draw.ellipse(
        (cx - badge_r, cy - badge_r, cx + badge_r, cy + badge_r),
        fill=(255, 255, 255, 235),
    )
    mono_font = _font(96)
    mono = _initials(product.title)
    mw = draw.textlength(mono, font=mono_font)
    draw.text(
        (cx - mw / 2, cy - 62), mono, font=mono_font, fill=(top[0], top[1], top[2])
    )

    # Category chip.
    if root_name:
        chip_font = _font(30, bold=True)
        label = root_name.upper()
        lw = draw.textlength(label, font=chip_font)
        pad = 24
        chip_w, chip_h = lw + pad * 2, 56
        chip_x, chip_y = cx - chip_w / 2, 470
        draw.rounded_rectangle(
            (chip_x, chip_y, chip_x + chip_w, chip_y + chip_h),
            radius=28,
            fill=(255, 255, 255, 60),
        )
        draw.text((chip_x + pad, chip_y + 12), label, font=chip_font, fill="white")

    # Product title, wrapped and centred.
    title_font = _font(56)
    lines = _wrap(draw, product.title, title_font, SIZE - 120)
    ty = 560
    for line in lines:
        tw = draw.textlength(line, font=title_font)
        draw.text((cx - tw / 2, ty), line, font=title_font, fill="white")
        ty += 64

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Generate branded placeholder images for seeded example products."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Regenerate existing images.")
        parser.add_argument(
            "--all",
            action="store_true",
            help="Cover all products, not just OASIS- seeded ones.",
        )

    def handle(self, *args, **options):
        qs = Product.objects.all()
        if not options["all"]:
            qs = qs.filter(upc__startswith="OASIS-")

        made, skipped = 0, 0
        for product in qs.iterator():
            has_image = product.images.exists()
            if has_image and not options["force"]:
                skipped += 1
                continue
            if has_image and options["force"]:
                product.images.all().delete()

            data = render_product_image(product)
            image = ProductImage(product=product, display_order=0)
            image.original.save(
                "seed-%s.png" % (product.upc or product.pk), ContentFile(data), save=True
            )
            made += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Images: %d generated, %d skipped (already had one)." % (made, skipped)
            )
        )
