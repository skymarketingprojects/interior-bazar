from django.db import migrations


# The four default home hero slides (task 74) — the prototype's ib-hero.js seed and
# the frontend's former static home.content.ts slides, now the backend seed of record.
# Buttons: (label, link, isPrimary). An empty link → the frontend adapter opens the
# project-intent connect wizard. Metrics: (metric, description).
DEFAULT_BANNERS = [
    {
        "tag": "attract. qualify. convert.",
        "title": "Find your perfect match.",
        "description": (
            "Interior bazzar runs the process your business never had time to build. "
            "We attract the right people, qualify their interest, intent, and urgency — "
            "then connect the genuine ones to you."
        ),
        "gradient": "green",
        "buttons": [("Find your match", "", True), ("List your business", "/plans", False)],
        "metrics": [("500+", "Verified businesses"), ("120/mo", "Projects matched"), ("4.8 ★", "5-star rated")],
    },
    {
        "tag": "Seller growth platform",
        "title": "Stop chasing clients. Let them find you.",
        "description": (
            "3-step qualification filters every enquiry by contact, genuineness and urgency "
            "before it reaches you. No more cold chasing — only genuine buyers."
        ),
        "gradient": "amber",
        "buttons": [("List my business", "/plans", True), ("See plans", "/plans", False)],
        "metrics": [("3×", "Higher close rate"), ("₹0", "Commission on deals"), ("48h", "Avg. first connection")],
    },
    {
        "tag": "India's verified network",
        "title": "Every business. Every review. Verified.",
        "description": (
            "Manual verification, not algorithms. Every listing reviewed by a human. "
            "Every review from a real buyer. The only platform where trust is the product."
        ),
        "gradient": "navy",
        "buttons": [("Browse businesses", "/businesses", True), ("How it works", "/help", False)],
        "metrics": [("100%", "Manual verified"), ("28+", "Indian cities"), ("MSME", "Govt. registered")],
    },
    {
        "tag": "Made for India",
        "title": "Designed for India's design industry.",
        "description": (
            "UPI payments. Hindi interface coming. Regional cities prioritised. "
            "Built from New Delhi, for every city where great design happens."
        ),
        "gradient": "plum",
        "buttons": [("Explore near me", "/businesses", True), ("About IB", "/help", False)],
        "metrics": [("\U0001f1ee\U0001f1f3", "India-first"), ("UPI", "Native payments"), ("हिन्दी", "Coming soon")],
    },
]


def seed_home_banners(apps, schema_editor):
    HomeHeroBanner = apps.get_model("interior_advertisement", "HomeHeroBanner")
    BannerButton = apps.get_model("interior_advertisement", "BannerButton")
    BannerMetric = apps.get_model("interior_advertisement", "BannerMetric")
    # Idempotent: only seed when a fresh DB has no home banners — never duplicate the
    # editor's live banners.
    if HomeHeroBanner.objects.filter(page="home").exists():
        return
    for order, b in enumerate(DEFAULT_BANNERS):
        banner = HomeHeroBanner.objects.create(
            page="home", tag=b["tag"], title=b["title"], description=b["description"],
            backgroundGradient=b["gradient"], displayOrder=order, isActive=True,
        )
        for label, link, is_primary in b["buttons"]:
            BannerButton.objects.create(banner=banner, label=label, link=link, isPrimary=is_primary)
        for idx, (metric, desc) in enumerate(b["metrics"]):
            BannerMetric.objects.create(banner=banner, metric=metric, description=desc, index=idx)


def unseed_home_banners(apps, schema_editor):
    # Reverse is a no-op: we can't tell seeded rows from editor-created ones, and the
    # forward op is guarded, so leave existing banners untouched on rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("interior_advertisement", "0005_homeherobanner_page"),
    ]

    operations = [
        migrations.RunPython(seed_home_banners, unseed_home_banners),
    ]
