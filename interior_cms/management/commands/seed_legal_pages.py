"""
Loads the real legal copy (terms / privacy / refund / cookies / disclaimer) from
interior_cms/data/legal_pages.json into Pages, which the v3 legal pages render via
GET /api/v1/page/<pageName>/.

The JSON is the <article class="lx-art"> body of each prototype page, lifted verbatim —
the prototype is the source of truth for this copy. The lx-* classes are intentional:
LegalV3.module.css styles :global(.lx-sec) / :global(.lx-intro), and useLegalV3 builds
the "On this page" TOC from the <section id>/<h2> pairs in this HTML.

Unlike app_ib.0040_full_legal_page_copy (which skips any page that already has real
content, so prod-restored copy survives), this OVERWRITES — that migration is why dev
and stage were still serving older, shorter copy.

Idempotent: re-running writes the same bytes.

Both cache layers are cleared per page — there are two, and clearing only one
leaves stale copy served for up to 24h:
  * GetPagesView            -> "cache:page:<name>"   (12h)
  * PAGE_CONTROLLER.GetPages -> "static_page_<name>"  (24h, read first)
"""
import json
from pathlib import Path

from django.core.cache import cache
from django.core.management.base import BaseCommand

from interior_cms.models import Pages

DATA = Path(__file__).resolve().parent.parent.parent / "data" / "legal_pages.json"


class Command(BaseCommand):
    help = "Load real legal page copy from interior_cms/data/legal_pages.json into Pages."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing.",
        )

    def handle(self, *args, **options):
        pages = json.loads(DATA.read_text(encoding="utf-8"))
        dry = options["dry_run"]

        for page in pages:
            slug, title, html = page["pageName"], page["title"], page["html"]
            # QuillField stores {"delta": ..., "html": ...}; delta stays empty exactly as
            # 0034/0040 seeded it — the editor rebuilds it from html on first admin save.
            quill_json = json.dumps({"delta": "", "html": html})

            obj = Pages.objects.filter(pageName=slug).first()
            before = 0
            if obj:
                raw = Pages.objects.filter(pk=obj.pk).values_list("content", flat=True).first()
                try:
                    before = len(json.loads(raw or "{}").get("html", "") or "")
                except (ValueError, AttributeError):
                    before = 0

            verb = "would write" if dry else "wrote"
            if not dry:
                Pages.objects.update_or_create(
                    pageName=slug,
                    defaults={"title": title, "content": quill_json},
                )
                cache.delete_many([f"cache:page:{slug}", f"static_page_{slug}"])

            self.stdout.write(
                f"{verb} {slug:24} {before:>6} -> {len(html):<6} chars  ({title})"
            )

        self.stdout.write(self.style.SUCCESS(f"{len(pages)} legal pages processed"))
