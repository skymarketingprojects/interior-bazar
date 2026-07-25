"""
Dev-data repair: give every Business a Location row.

WHY: `AdsQueryView.CreateAdsQueryView` and `QueryView.CreateQueryView` both do

    location = user.user_business.business_location
    reqdata['state'] = location.locationState.name

with no null-guard, so for an authenticated BUSINESS user whose Business has no
Location the request dies with
`RelatedObjectDoesNotExist: Business has no business_location.` and the API
returns `{"response": false, "code": 202, "message": "Unable to generate ads query"}`.

On this dev DB ALL businesses were missing a Location, so the "Get best deal"
ads form was broken for every logged-in seller. Found during the 2026-07-24
end-to-end QA sweep.

This only fills MISSING rows — existing Locations are never touched. Idempotent.

NOTE: this repairs the DATA. The missing null-guard in the two views is a
separate (pre-existing) code bug and is deliberately left alone here.
"""
from django.core.management.base import BaseCommand

from app_ib.models import Location
from interior_business.models import Business


class Command(BaseCommand):
    help = "Create a Location for every Business that doesn't have one (dev data repair)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be created without writing anything.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]

        template = Location.objects.filter(
            locationState__isnull=False, locationCountry__isnull=False
        ).first()
        if template is None:
            self.stderr.write(
                self.style.ERROR(
                    "No Location with both state and country exists to copy from — aborting."
                )
            )
            return

        missing = [b for b in Business.objects.all() if not Location.objects.filter(business=b).exists()]
        self.stdout.write(
            f"businesses={Business.objects.count()} missing_location={len(missing)} "
            f"template=({template.city}, {template.locationState}, {template.locationCountry})"
        )

        if dry:
            for b in missing:
                self.stdout.write(f"  would create Location for #{b.pk} {b}")
            return

        created = 0
        for b in missing:
            Location.objects.create(
                business=b,
                city=template.city,
                pinCode=template.pinCode,
                locationState=template.locationState,
                locationCountry=template.locationCountry,
            )
            created += 1

        still = sum(1 for b in Business.objects.all() if not Location.objects.filter(business=b).exists())
        self.stdout.write(self.style.SUCCESS(f"created={created} still_missing={still}"))
