from django.db import migrations


def seed_support_config(apps, schema_editor):
    SupportConfig = apps.get_model("app_ib", "SupportConfig")
    # Idempotent singleton seed with the REAL support channels (from the legal pages /
    # frontend contact constants). tollFree is empty and liveChatAvailable is False —
    # no fabricated toll-free number or fake "agents online" count.
    if SupportConfig.objects.exists():
        return
    SupportConfig.objects.create(
        supportEmail="help@interiorbazzar.com",
        phone="+91 88823 14255",
        whatsapp="918920898168",
        tollFree="",
        officeAddress=(
            "Plot no-42 First Floor, Kh no-27/14 Shiv Park, Kakrola, "
            "New Delhi, South West Delhi 110078, Delhi"
        ),
        hours="Mon–Sat · 9 AM – 9 PM IST",
        liveChatAvailable=False,
        agentCount=0,
    )


def unseed_support_config(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0048_supportconfig"),
    ]

    operations = [
        migrations.RunPython(seed_support_config, unseed_support_config),
    ]
