"""The resolved admin RBAC matrix (workflows/admin-rbac-plan.md, promptsadmin
task 55). Level per (module, role): 0 none / 1 read / 2 write / 3 sensitive.
Role order matches ROLES. super_admin is is_full_access → 3 everywhere at runtime,
but seeded explicitly too so the roles-editor grid shows real values."""

ROLES = ["super_admin", "ops_manager", "finance", "sales_agent", "content", "catalog_mod", "analyst"]

# module -> [SA, OM, FI, SL, CO, CM, AN]
MATRIX = {
    "overview":      [3, 1, 1, 1, 1, 1, 1],
    "plans":         [3, 1, 1, 0, 0, 0, 1],
    "banners-house": [3, 1, 0, 0, 2, 0, 1],
    "banners-ad":    [3, 2, 1, 0, 2, 0, 1],
    "templates":     [3, 1, 0, 0, 2, 0, 1],
    "buyers":        [3, 1, 1, 1, 0, 0, 1],
    "businesses":    [3, 2, 1, 1, 0, 2, 1],
    "subs":          [3, 1, 1, 0, 0, 0, 1],
    "slots":         [3, 2, 1, 1, 0, 0, 1],
    "payments":      [3, 2, 1, 0, 0, 0, 1],
    "refunds":       [3, 0, 3, 0, 0, 0, 0],
    "routing":       [3, 2, 0, 2, 0, 0, 1],
    "quarantine":    [3, 2, 0, 1, 0, 0, 1],
    "weights":       [3, 1, 0, 0, 0, 0, 1],
    "web":           [3, 1, 1, 1, 1, 0, 1],
    "revenue":       [3, 1, 3, 0, 0, 0, 1],
    "cat-biz":       [3, 2, 0, 0, 0, 2, 1],
    "reviews":       [3, 2, 0, 0, 0, 2, 1],
    "testimonials":  [3, 0, 0, 0, 0, 0, 0],
    "reports":       [3, 2, 0, 1, 0, 2, 1],
    "cat-region":    [3, 2, 0, 0, 0, 2, 1],
    "feedback":      [3, 2, 0, 0, 1, 0, 1],
    "plan-requests": [3, 2, 2, 0, 0, 0, 1],
    "content":       [3, 0, 0, 0, 2, 0, 1],
    "support":       [3, 2, 0, 2, 0, 0, 1],
    "brand-logo":    [3, 0, 0, 0, 0, 0, 0],
    "roles":         [3, 0, 0, 0, 0, 0, 0],
    "audit":         [3, 1, 1, 0, 0, 0, 1],
}

MODULE_KEYS = list(MATRIX.keys())


def levels_for_role(role_name: str) -> dict:
    """{moduleKey: level} for a role name from the static matrix."""
    if role_name not in ROLES:
        return {}
    idx = ROLES.index(role_name)
    return {mod: levels[idx] for mod, levels in MATRIX.items()}


def seed_roles_and_matrix():
    """Idempotent: create the 7 ops Roles + seed AdminModuleAccess rows from the
    matrix. Safe to re-run (get_or_create); does NOT overwrite admin edits made
    via the roles editor (only fills missing rows). Sync — call from a mgmt
    command or migration, not an async request."""
    from rbac_module.models import Role
    from interior_admin.models import AdminModuleAccess
    created = {"roles": 0, "cells": 0}
    for name in ROLES:
        role, was_new = Role.objects.get_or_create(
            name=name, defaults={"is_full_access": name == "super_admin"})
        if was_new:
            created["roles"] += 1
        for mod, level in levels_for_role(name).items():
            _, cell_new = AdminModuleAccess.objects.get_or_create(
                role=role, moduleKey=mod, defaults={"level": level})
            if cell_new:
                created["cells"] += 1
    return created
