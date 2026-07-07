from django.core.management.base import BaseCommand
from interior_admin.Controllers.Roles.rbac_matrix import seed_roles_and_matrix


class Command(BaseCommand):
    help = "Idempotently seed the 7 ops Roles + admin RBAC matrix (promptsadmin task 55). Run on deploy."

    def handle(self, *args, **options):
        created = seed_roles_and_matrix()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded admin roles: +{created['roles']} roles, +{created['cells']} matrix cells (idempotent)."))
