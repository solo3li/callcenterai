from django.core.management.base import BaseCommand

from knowledge.models import Document, DocumentChunk
from knowledge.services import process_document


class Command(BaseCommand):
    help = (
        "Wipe all stored chunks and re-embed every document with the current "
        "embedding model. Run this after switching embedding models (e.g. "
        "OpenAI text-embedding-3-small -> Gemini gemini-embedding-001): vectors "
        "from different models are not comparable."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-chunks",
            action="store_true",
            help="Do not delete existing chunks before re-embedding.",
        )

    def handle(self, *args, **options):
        if not options["keep_chunks"]:
            total, _ = DocumentChunk.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {total} existing chunks."))

        docs = Document.objects.all()
        self.stdout.write(f"Re-embedding {docs.count()} document(s)...")

        completed, failed = 0, 0
        for doc in docs:
            process_document(doc.id)
            doc.refresh_from_db()
            if doc.status == "COMPLETED":
                completed += 1
                self.stdout.write(self.style.SUCCESS(f"  [OK] {doc.file_name}"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  [FAILED] {doc.file_name}"))

        self.stdout.write(
            self.style.SUCCESS(f"Done. completed={completed}, failed={failed}")
        )
