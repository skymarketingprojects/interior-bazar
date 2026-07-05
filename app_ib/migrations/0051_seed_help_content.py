# -*- coding: utf-8 -*-
from django.db import migrations


FAQS = [
    ("How do I send an enquiry to a business?",
     "Open any business or product profile and tap <strong>Send enquiry</strong>. Fill in a quick brief — budget, timeline, location, what you need. The business gets your enquiry instantly and most reply within 12 minutes."),
    ("Is it free for me as a buyer?",
     "Yes — sending enquiries, browsing profiles, saving items, and chatting with businesses is completely free for buyers. We only charge businesses for premium plans and verified listings."),
    ("How are businesses verified?",
     "Verified businesses (★ badge) have submitted proof of identity, GST/tax ID, business address, and at least 3 completed projects. We also re-verify every 12 months."),
    ("Can I change my mind after sending an enquiry?",
     "Of course. You can withdraw an enquiry, ask the business not to contact you, or block any business from your account settings. No penalty either way."),
    ("What if I have a dispute with a business?",
     "Open the ticket from Help & Support, attach screenshots or messages, and our trust & safety team will mediate within 48 hours. We hold seller payouts during open disputes."),
    ("How do I become a seller on Interior bazzar?",
     "From the profile dropdown, choose <strong>Become a member</strong>. Pick a plan, register your business, and you'll go live within 48 hours after verification."),
]

TOPICS = [
    ("Account & profile", "ti-user", "#e1f5ee", "#085041", 14),
    ("Enquiries & messaging", "ti-send", "#fef3e0", "#ba7517", 11),
    ("Billing & plans", "ti-credit-card", "#e8f0fa", "#185fa5", 9),
    ("Trust & safety", "ti-shield-check", "#eeedfe", "#3c3489", 8),
    ("Become a seller", "ti-building-store", "#fdebe5", "#d44323", 12),
    ("Orders & deliveries", "ti-package", "#e1f5ee", "#085041", 7),
    ("Refunds & returns", "ti-refresh", "#fef3e0", "#ba7517", 6),
    ("Report a bug", "ti-bug", "#e8f0fa", "#185fa5", 5),
]

TUTORIALS = [
    ("Sending your first enquiry", "linear-gradient(135deg,#085041,#1d9e75)", "2:14", "8,420 views"),
    ("Saving & organising profiles", "linear-gradient(135deg,#04342c,#1d9e75)", "1:48", "5,210 views"),
    ("Picking the right architect", "linear-gradient(135deg,#5c3008,#d4823a)", "3:02", "12,180 views"),
    ("Becoming a seller in 5 steps", "linear-gradient(135deg,#3c3489,#7a6dd5)", "2:40", "3,420 views"),
]


def seed_help(apps, schema_editor):
    HelpFaq = apps.get_model("app_ib", "HelpFaq")
    HelpTopic = apps.get_model("app_ib", "HelpTopic")
    HelpTutorial = apps.get_model("app_ib", "HelpTutorial")
    if not HelpFaq.objects.exists():
        for i, (q, a) in enumerate(FAQS):
            HelpFaq.objects.create(question=q, answer=a, displayOrder=i)
    if not HelpTopic.objects.exists():
        for i, (title, icon, bg, color, count) in enumerate(TOPICS):
            HelpTopic.objects.create(title=title, icon=icon, iconBg=bg, iconColor=color,
                                     articleCount=count, displayOrder=i)
    if not HelpTutorial.objects.exists():
        for i, (title, grad, dur, views) in enumerate(TUTORIALS):
            HelpTutorial.objects.create(title=title, gradient=grad, duration=dur,
                                        views=views, displayOrder=i)


def unseed_help(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0050_helpfaq_helptopic_helptutorial_supportticket"),
    ]

    operations = [
        migrations.RunPython(seed_help, unseed_help),
    ]
