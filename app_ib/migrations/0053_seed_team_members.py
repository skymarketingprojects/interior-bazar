from django.db import migrations


MEMBERS = [
    ("Vishal Shakya", "Founder · CEO", "VS", "linear-gradient(135deg,#085041,#1d9e75)",
     "Builder. Has spent most of his career deep in technology — not to build for the sake of it, but to solve problems that matter.", False),
    ("Interior bazzar Team", "Design · Engineering · Ops", "IB", "linear-gradient(135deg,#3c3489,#6b63c9)",
     "A growing team across product, design, and operations. We're hiring people who care about India's built environment.", False),
    ("We're hiring", "Join us", "+", "#e5e2d9",
     "We're looking for people who want to build something real for India's interior industry. Say hi.", True),
]


def seed_team(apps, schema_editor):
    TeamMember = apps.get_model("app_ib", "TeamMember")
    if TeamMember.objects.exists():
        return
    for i, (name, role, initials, gradient, bio, placeholder) in enumerate(MEMBERS):
        TeamMember.objects.create(name=name, role=role, initials=initials, gradient=gradient,
                                  bio=bio, isPlaceholder=placeholder, displayOrder=i)


def unseed_team(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0052_teammember"),
    ]

    operations = [
        migrations.RunPython(seed_team, unseed_team),
    ]
