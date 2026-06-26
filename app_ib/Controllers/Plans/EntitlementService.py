"""
EntitlementService — the single chokepoint for "what plans does a user hold and what
do they unlock". Collapses the per-entityType branching that used to be duplicated
across PlanController / GapsController / CrudController into one registry + helpers.

Design (buy-first subscription model):
  • One plan model per entity family: BusinessPlan / ShopPlan / ArchitectPlan, plus the
    AutomationPlan BUNDLE (entity-less; unlocks all three tabs).
  • A plan's `status` (PLAN_STATUS) is the lifecycle source of truth; isActive is a
    derived shim.
  • What a plan UNLOCKS is data, not code: Subscription.grantsEntityTypes (automation →
    [business, shop, architect]; every other → [its own type]). Adding a new bundle or
    entity type is a seed-row + (for a new entity) one nullable FK — never a code sweep.

All methods are sync (Django ORM); async callers wrap with sync_to_async.
"""
from django.utils import timezone

from app_ib.Utils.EngineConfig import ENTITY_TYPE, PLAN_STATUS, PLAN_GRANTS, PLAN_FAMILY


# entityType → the FK attribute that points at the linked entity on a per-type plan.
ENTITY_FK = {
    ENTITY_TYPE.BUSINESS: "business",
    ENTITY_TYPE.SHOP: "shop",
    ENTITY_TYPE.ARCHITECT: "architect",
}


class _EntitlementService:

    # ── registry ───────────────────────────────────────────────────────────────
    def models(self):
        """entityType → plan model. Lazy import to dodge app-loading cycles."""
        from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan
        return {
            ENTITY_TYPE.BUSINESS: BusinessPlan,
            ENTITY_TYPE.SHOP: ShopPlan,
            ENTITY_TYPE.ARCHITECT: ArchitectPlan,
            ENTITY_TYPE.AUTOMATION: AutomationPlan,
        }

    def model_for(self, entity_type):
        # default to BusinessPlan to mirror the legacy fallback behaviour.
        from app_ib.models import BusinessPlan
        return self.models().get(entity_type, BusinessPlan)

    def model_for_family(self, plan_family):
        """The plan model a Subscription should create rows in, by planFamily.
        Automation → AutomationPlan; everything else → its entity plan."""
        if plan_family == PLAN_FAMILY.AUTOMATION:
            return self.model_for(ENTITY_TYPE.AUTOMATION)
        return self.model_for(plan_family)

    # ── grants ─────────────────────────────────────────────────────────────────
    def grants_for(self, instance):
        """Entity tabs this purchased plan unlocks. Reads the catalogue
        Subscription.grantsEntityTypes; falls back to the plan family if a legacy row
        has none."""
        sub = getattr(instance, "plan", None)
        grants = list(getattr(sub, "grantsEntityTypes", None) or [])
        if grants:
            return grants
        family = getattr(sub, "planFamily", None) or getattr(sub, "entityType", None)
        return list(PLAN_GRANTS.get(family, []))

    # ── serialization (matches the existing my/plans item shape) ───────────────
    def serialize(self, instance, entity_type):
        entity = None
        if entity_type in ENTITY_FK:
            entity = getattr(instance, ENTITY_FK[entity_type], None)
        sub = getattr(instance, "plan", None)
        return {
            "id": instance.id,
            "entityType": entity_type,
            "entityId": entity.id if entity else None,
            "planId": instance.plan_id,
            "planName": sub.title if sub else None,
            "tier": sub.tier if sub else None,
            "amount": instance.amount,
            "isActive": instance.isActive,
            "status": instance.status,
            "transactionId": instance.transactionId,
            "expireDate": instance.expireDate.strftime("%Y-%m-%d") if instance.expireDate else None,
            "lastActivate": instance.lastActivate.strftime("%Y-%m-%d") if instance.lastActivate else None,
            "timestamp": instance.timestamp.strftime("%Y-%m-%d") if instance.timestamp else None,
        }

    # ── reads ──────────────────────────────────────────────────────────────────
    def iter_rows(self, user):
        """Yield (entity_type, instance) for every plan the user owns, newest first.
        Covers buy-first rows (user FK) and legacy business rows linked via business.user."""
        from django.db.models import Q
        from app_ib.models import BusinessPlan
        for entity_type, Model in self.models().items():
            if Model is BusinessPlan:
                qs = (Model.objects.filter(Q(user=user) | Q(business__user=user))
                      .select_related("plan", "business").order_by("-timestamp"))
            else:
                related = ["plan"] + ([ENTITY_FK[entity_type]] if entity_type in ENTITY_FK else [])
                qs = Model.objects.filter(user=user).select_related(*related).order_by("-timestamp")
            for ins in qs:
                yield entity_type, ins

    def my_plans(self, user):
        """Buying history + the two entitlement signals.
          • activeEntityTypes   — grants of ACTIVE plans → gate publishing / entity creation.
          • entitledEntityTypes — grants of active-OR-pending plans → gate TAB VISIBILITY.
        Automation expands to all three in both, purely via grantsEntityTypes."""
        items, active, entitled = [], set(), set()
        for entity_type, ins in self.iter_rows(user):
            items.append(self.serialize(ins, entity_type))
            grants = self.grants_for(ins)
            if ins.status == PLAN_STATUS.ACTIVE:
                active.update(grants)
                entitled.update(grants)
            elif ins.status in PLAN_STATUS.ENTITLED:  # pending
                entitled.update(grants)
        return {
            "items": items,
            "total": len(items),
            "activeEntityTypes": sorted(active),
            "entitledEntityTypes": sorted(entitled),
        }

    # ── entity-creation gate / linking ─────────────────────────────────────────
    def active_entitlement_for(self, user, entity_type):
        """The plan instance that authorizes creating an entity of `entity_type`: an
        ACTIVE plan that grants it and still has that entity slot free. Prefers a
        dedicated per-type plan; falls back to an automation bundle (whose matching
        nullable FK is empty). Returns (instance, entity_type_of_instance) or (None, None)."""
        fk = ENTITY_FK.get(entity_type)
        if not fk:
            return None, None
        # 1) dedicated per-type plan
        Model = self.model_for(entity_type)
        plan = (Model.objects.filter(user=user, status=PLAN_STATUS.ACTIVE,
                                     **{f"{fk}__isnull": True}).order_by("-timestamp").first())
        if plan:
            return plan, entity_type
        # 2) automation bundle that grants this entity, with its slot free
        Automation = self.model_for(ENTITY_TYPE.AUTOMATION)
        auto = (Automation.objects.filter(user=user, status=PLAN_STATUS.ACTIVE,
                                          **{f"{fk}__isnull": True})
                .select_related("plan").order_by("-timestamp"))
        for a in auto:
            if entity_type in self.grants_for(a):
                return a, ENTITY_TYPE.AUTOMATION
        return None, None

    def link_entity(self, user, entity_type, entity):
        """Fill the nullable entity FK on the authorizing plan (per-type or automation).
        Raises Conflict_ if the user holds no active plan granting this entity."""
        from app_ib.Controllers.Engine.CrudController import Conflict_
        plan, _ = self.active_entitlement_for(user, entity_type)
        if not plan:
            raise Conflict_(f"No active {entity_type} subscription to link — buy a plan first")
        setattr(plan, ENTITY_FK[entity_type], entity)
        plan.save()
        return plan


ENTITLEMENT_SERVICE = _EntitlementService()
