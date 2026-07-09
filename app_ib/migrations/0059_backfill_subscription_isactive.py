from django.db import migrations


def backfill_is_active(apps, schema_editor):
    # The public plans list previously returned ALL Subscription rows regardless
    # of isActive. Now that buyers are filtered to isActive=True, activate every
    # existing row so the pre-change visible set is preserved (else the public
    # plans page goes blank for any row seeded/created with the default False).
    Subscription = apps.get_model("app_ib", "Subscription")
    Subscription.objects.filter(isActive=False).update(isActive=True)


def noop_reverse(apps, schema_editor):
    # One-way backfill — reversing would re-hide plans arbitrarily.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0058_alter_banners_options_banners_bannerurl_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_is_active, noop_reverse),
    ]
