"""Data migration (Phase 1, buy-first subscription redesign):

  • Subscription  — backfill planFamily (from legacy entityType) + grantsEntityTypes
    (automation → all three tabs; every other family → its own tab).
  • BusinessPlan / ShopPlan / ArchitectPlan — backfill the new `status` lifecycle from
    the legacy isActive flag: active → ACTIVE, else past expireDate → EXPIRED, else PENDING.

Additive + reversible-as-noop. Mirrors the model save() logic so new + old rows agree.
"""
from django.db import migrations
from django.utils import timezone

from app_ib.Utils.EngineConfig import PLAN_STATUS, PLAN_FAMILY, PLAN_GRANTS, ENTITY_TYPE


def _grants_for(family, entity_type):
    return list(PLAN_GRANTS.get(family, [entity_type or ENTITY_TYPE.BUSINESS]))


def forwards(apps, schema_editor):
    Subscription = apps.get_model("app_ib", "Subscription")
    for sub in Subscription.objects.all():
        # planFamily is a brand-new column (every existing row just got the model
        # default), so the legacy `entityType` is the real source of truth here.
        family = sub.entityType or PLAN_FAMILY.BUSINESS
        sub.planFamily = family
        if not sub.grantsEntityTypes:
            sub.grantsEntityTypes = _grants_for(family, sub.entityType)
        sub.save(update_fields=["planFamily", "grantsEntityTypes"])

    now = timezone.now()
    for model_name in ("BusinessPlan", "ShopPlan", "ArchitectPlan"):
        Model = apps.get_model("app_ib", model_name)
        for plan in Model.objects.all():
            if plan.isActive:
                plan.status = PLAN_STATUS.ACTIVE
            elif plan.expireDate and plan.expireDate < now:
                plan.status = PLAN_STATUS.EXPIRED
            else:
                plan.status = PLAN_STATUS.PENDING
            plan.save(update_fields=["status"])


def backwards(apps, schema_editor):
    # Fields are dropped by the reverse of 0031; nothing to undo here.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_ib", "0031_architectplan_status_businessplan_status_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
