import json

from django.db import migrations

PAGES = [
    {
        "pageName": "terms-and-conditions",
        "title": "Terms & Conditions",
        "html": '<p>These terms govern your use of Interior bazzar, operated by Feelsafe Technology India Pvt Ltd. By accessing the platform you agree to be bound by them.</p><h2>1. Use of the platform</h2><p>Interior bazzar is a discovery and enquiry platform connecting buyers with verified interior professionals. We facilitate introductions; we are not a party to any contract you form with a listed business.</p><p>You agree to use the platform lawfully and to provide accurate information when sending enquiries or creating a listing.</p><h2>2. Listings &amp; verification</h2><p>Business listings are reviewed before going live. We do not guarantee the quality, pricing, or outcome of any service obtained through a listed professional.</p><h2>3. Payments</h2><p>Subscription and listing fees are described on the Plans page. Fees are billed in advance and are subject to our refund policy.</p><h2>4. Limitation of liability</h2><p>To the maximum extent permitted by law, Interior bazzar is not liable for indirect or consequential losses arising from your use of the platform or any transaction with a listed business.</p>',
    },
    {
        "pageName": "privacy-policy",
        "title": "Privacy Policy",
        "html": '<p>This policy explains how Interior bazzar collects, uses, and protects your personal information.</p><h2>1. Information we collect</h2><p>We collect information you provide directly — name, contact details, and enquiry content — as well as basic usage data to improve the platform.</p><h2>2. How we use it</h2><p>We use your information to route enquiries to the right professional, verify genuineness, prevent spam, and operate and improve the service.</p><h2>3. Sharing</h2><p>When you send an enquiry, relevant details are shared with the business you contacted. We do not sell your personal data.</p><h2>4. Your rights</h2><p>You may request access to, correction of, or deletion of your personal data by contacting us at help@interiorbazzar.com.</p>',
    },
    {
        "pageName": "return-and-refund",
        "title": "Return & Refund Policy",
        "html": '<p>This policy explains refund eligibility for Interior bazzar subscriptions and listing fees.</p><h2>1. Subscriptions</h2><p>Subscription fees are billed in advance. You may cancel at any time; cancellation stops future billing but does not retroactively refund the current period unless required by law.</p><h2>2. Eligibility</h2><p>Refund requests within 7 days of a first purchase are reviewed case by case. Fees for services already rendered or leads already delivered are non-refundable.</p><h2>3. How to request</h2><p>Email help@interiorbazzar.com with your account details and reason. Approved refunds are processed to the original payment method within 7–10 business days.</p>',
    },
    {
        "pageName": "disclaimer",
        "title": "Disclaimer",
        "html": '<p>Interior bazzar provides a discovery and enquiry platform. This disclaimer outlines the limits of our responsibility.</p><h2>1. No endorsement</h2><p>Listing a business on Interior bazzar does not constitute an endorsement. Buyers should perform their own due diligence before engaging any professional.</p><h2>2. Accuracy</h2><p>While we verify listings, we do not guarantee that all information is current or error-free. Pricing, availability, and portfolios are provided by the businesses themselves.</p><h2>3. Third-party content</h2><p>The platform may reference third-party content or links. We are not responsible for the content or practices of third parties.</p>',
    },
    {
        "pageName": "cookie-policy",
        "title": "Cookie Policy",
        "html": '<p>This policy explains how Interior bazzar uses cookies and similar technologies.</p><h2>1. What cookies we use</h2><p>We use essential cookies to keep you signed in and remember your preferences, and analytics cookies to understand how the platform is used.</p><h2>2. Managing cookies</h2><p>You can control or delete cookies through your browser settings. Disabling essential cookies may affect core functionality.</p><h2>3. Contact</h2><p>Questions about this policy can be sent to help@interiorbazzar.com.</p>',
    },
]


def seed_pages(apps, schema_editor):
    Pages = apps.get_model("app_ib", "Pages")
    for page in PAGES:
        quill_json = json.dumps({"delta": "", "html": page["html"]})
        obj, created = Pages.objects.get_or_create(
            pageName=page["pageName"],
            defaults={"title": page["title"], "content": quill_json},
        )
        if not created:
            obj.title = page["title"]
            obj.content = quill_json
            obj.save()


def remove_pages(apps, schema_editor):
    Pages = apps.get_model("app_ib", "Pages")
    Pages.objects.filter(pageName__in=[p["pageName"] for p in PAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0033_business_isactive"),
    ]

    operations = [
        migrations.RunPython(seed_pages, remove_pages),
    ]
