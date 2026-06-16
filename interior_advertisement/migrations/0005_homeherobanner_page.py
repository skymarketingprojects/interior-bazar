from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("interior_advertisement", "0004_homeherobanner_bannermetric_bannerbutton"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeherobanner",
            name="page",
            field=models.CharField(
                choices=[
                    ("home", "Home"),
                    ("architects", "Architects"),
                    ("shops", "Shops"),
                    ("products", "Products"),
                    ("businesses", "Businesses"),
                    ("catalogues", "Catalogues"),
                    ("about", "About"),
                    ("blog", "Blog"),
                    ("explore", "Explore"),
                    ("contact", "Contact"),
                ],
                db_index=True,
                default="home",
                max_length=40,
            ),
        ),
    ]
