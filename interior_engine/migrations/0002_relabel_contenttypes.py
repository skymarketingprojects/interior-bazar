"""TASK 13 follow-up: consolidate ContentType rows for the moved discovery-engine
models from app_label='app_ib' to 'interior_engine'.

After the state-only model move, `ContentType.objects.get_for_model(Shop)` resolves
to a NEW (interior_engine, shop) row, while existing generic-FK data (ViewEvent /
TrendingScore / SavedItem / analytics ...) still references the original
(app_ib, shop) row. Left split, that data would be silently orphaned.

Fix per moved model: repoint any GFK references off the new (usually-empty) dup
onto the original row, delete the dup, then relabel the original -> interior_engine
(id preserved, so all existing references stay valid). No-op on a fresh DB (no
app_ib row to relabel). Reversible.
"""
from django.db import migrations

# concrete model names moved app_ib -> interior_engine (TASK 13). GenericContentBase
# is abstract (no ContentType). Model names are lowercased (ContentType.model).
MOVED = [
    "genericcontentbase",  # harmless if absent (abstract -> no ct row)
    "platform", "architect", "shop", "testimonial", "contactinfo", "award",
    "processstep", "review", "reviewimage", "viewevent", "searchevent", "clickevent",
    "trendingscore", "leaderboardentry", "behindthetrendstory", "saveditem",
    "recentlyviewed", "engagementactivity", "businessteammember", "businessanalytics",
    "tag", "feedevent", "syntheticeventtemplate", "shortvideolink", "fallbackvideo",
    "project", "editorspick", "autogrowthkeyword", "dailysnapshot", "relateditem",
    "businessspecialization", "specializationjob", "differentiator", "joinuscta",
    "joinusstep", "shopupdate", "shopquestion", "shopimage",
]


# Framework tables keep their own per-ContentType rows (auth.Permission has a
# unique (content_type, codename); the dup ct's auto-created permissions are
# cascade-deleted when we delete it). Only repoint app-level generic-FK data.
_FRAMEWORK_APPS = {"auth", "admin", "contenttypes", "sessions", "sites"}


def _ct_fk_columns(apps):
    """(model_class, attname) for every concrete app FK pointing at ContentType."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    out = []
    for model in apps.get_models():
        if model._meta.app_label in _FRAMEWORK_APPS:
            continue
        for f in model._meta.get_fields():
            if getattr(f, "many_to_one", False) and f.related_model is ContentType:
                out.append((model, f.attname))  # e.g. contentType_id
    return out


def _consolidate(apps, from_label, to_label):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ct_cols = _ct_fk_columns(apps)
    for model_name in MOVED:
        old = ContentType.objects.filter(app_label=from_label, model=model_name).first()
        new = ContentType.objects.filter(app_label=to_label, model=model_name).first()
        if old is None:
            continue  # fresh DB / nothing to move
        if new is not None:
            # defensively move any refs off the dup, then drop it
            for mdl, col in ct_cols:
                mdl.objects.filter(**{col: new.id}).update(**{col: old.id})
            new.delete()
        old.app_label = to_label
        old.save(update_fields=["app_label"])


def forwards(apps, schema_editor):
    _consolidate(apps, "app_ib", "interior_engine")


def backwards(apps, schema_editor):
    _consolidate(apps, "interior_engine", "app_ib")


class Migration(migrations.Migration):

    dependencies = [
        ("interior_engine", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
