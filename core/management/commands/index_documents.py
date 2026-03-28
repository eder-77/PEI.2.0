import os
from django.core.management.base import BaseCommand
from core.models import Document
from core.rag_service import index_document

class Command(BaseCommand):
    help = 'Indexe tous les documents PDF dans ChromaDB'

    def handle(self, *args, **kwargs):
        documents = Document.objects.all()
        total = documents.count()
        self.stdout.write(f"Indexation de {total} documents...")

        success = 0
        for doc in documents:
            try:
                chunks = index_document(doc)
                if chunks > 0:
                    self.stdout.write(f"✓ {doc.title} — {chunks} chunks")
                    success += 1
            except Exception as e:
                self.stdout.write(f"✗ {doc.title} — Erreur: {e}")

        self.stdout.write(f"\nTerminé: {success}/{total} documents indexés !")