"""Create the SERVICE category taxonomy and re-file every service onto it.

Services and products share one table (Service.category is an M2M to
ProductCategory), which let product categories — Furniture, Painting & Wall
Decor — leak into the services filter chips. The fix is a separate taxonomy in
the same table, marked by the `svc-` value prefix (SERVICE_CATEGORY_PREFIX), so
no schema change was needed.

TAXONOMY is the prototype's service list verbatim
(ibprototype/pages/services-mobile.html, const FILTERS), in its chip order.
RE_FILE maps the seeded service titles onto it by keyword — titles carry a city
suffix ("… - Mumbai"), so matching is substring-based, first rule wins, which is
why the specific rules are ordered before the general ones.

Idempotent: safe to re-run. Services whose title matches no rule keep whatever
categories they have and are reported, not guessed at.
"""
from django.core.management.base import BaseCommand

from interior_products.models import ProductCategory, Service, SERVICE_CATEGORY_PREFIX

P = SERVICE_CATEGORY_PREFIX

# (value, label) in prototype chip order; index is assigned from this order.
TAXONOMY = [
    (P + "interior-design", "Interior Design"),
    (P + "architecture", "Architecture"),
    (P + "modular-kitchen", "Modular Kitchen"),
    (P + "3d-visualisation", "3D Visualisation"),
    (P + "turnkey-execution", "Turnkey Execution"),
    (P + "deep-cleaning", "Deep Cleaning"),
    (P + "vastu-planning", "Vastu & Planning"),
    (P + "painting", "Painting"),
    (P + "electrical-mep", "Electrical & MEP"),
]

# (title keyword, category value) — first match wins, so order matters:
# "Modular Kitchen …" must be tested before the generic "interior design".
RE_FILE = [
    ("modular kitchen", P + "modular-kitchen"),
    ("3d interior visualization", P + "3d-visualisation"),
    ("vastu", P + "vastu-planning"),
    ("painting", P + "painting"),
    ("electrical wiring", P + "electrical-mep"),
    ("plumbing & sanitary", P + "electrical-mep"),
    ("turnkey", P + "turnkey-execution"),
    ("carpentry", P + "turnkey-execution"),
    ("false ceiling", P + "turnkey-execution"),
    ("wardrobe & storage", P + "turnkey-execution"),
    ("tile & flooring", P + "turnkey-execution"),
    ("bathroom renovation", P + "turnkey-execution"),
    ("renovation & remodeling", P + "architecture"),
    ("deep cleaning", P + "deep-cleaning"),
    # General interior-design work last.
    ("interior design", P + "interior-design"),
    ("living room makeover", P + "interior-design"),
    ("master bedroom", P + "interior-design"),
    ("office interior", P + "interior-design"),
    ("showroom interior", P + "interior-design"),
]


def categoryFor(title):
    t = (title or "").lower()
    for keyword, value in RE_FILE:
        if keyword in t:
            return value
    return None


class Command(BaseCommand):
    help = "Create the svc-* service category taxonomy and re-file services onto it."

    def handle(self, *args, **options):
        nextIndex = (ProductCategory.objects.order_by("-index").values_list("index", flat=True).first() or 0) + 1
        cats = {}
        for value, label in TAXONOMY:
            cat = ProductCategory.objects.filter(value=value).first()
            if not cat:
                cat = ProductCategory(value=value, lable=label, shortValue=label, index=nextIndex)
                cat.save()
                nextIndex += 1
                self.stdout.write(f"created category {value}")
            cats[value] = cat

        refiled, unmatched = 0, []
        for service in Service.objects.all():
            value = categoryFor(service.title)
            if not value:
                unmatched.append(service.title)
                continue
            # The service belongs to exactly one service category; set() drops
            # the old product category (Furniture/Home Decor) in the same call.
            service.category.set([cats[value]])
            refiled += 1

        self.stdout.write(self.style.SUCCESS(f"re-filed {refiled} services onto {len(cats)} service categories"))
        for title in unmatched:
            self.stdout.write(self.style.WARNING(f"  unmatched (left as-is): {title}"))
