from django.db import migrations, models


def publish_existing(apps, schema_editor):
    # `status` is added with default 'draft', but every blog that existed before
    # this change was already live on the public site. Flip them all to
    # 'published' so the public blog list/detail (now status='published' filtered)
    # keeps showing them — otherwise the /blog page goes blank.
    Blog = apps.get_model("app_ib", "Blog")
    Blog.objects.all().update(status="published")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0062_businesscategory_isactive_businesssegment_isactive"),
    ]

    operations = [
        migrations.AddField(
            model_name="blog",
            name="metaTitle",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.AddField(
            model_name="blog",
            name="metaDescription",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="blog",
            name="focusKeyword",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="blog",
            name="status",
            field=models.CharField(
                choices=[("draft", "draft"), ("published", "published")],
                default="draft",
                max_length=10,
            ),
        ),
        migrations.RunPython(publish_existing, noop_reverse),
    ]
