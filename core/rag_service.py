# core/rag_service.py
import os
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions
from django.conf import settings


# ── Configuration ChromaDB ──
CHROMA_PATH = os.path.join(settings.BASE_DIR, 'chroma_db')

# Utilise un modèle multilingue — supporte le français et l'arabe
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'

def get_chroma_client():
    """Retourne le client ChromaDB persistant"""
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_collection():
    """Retourne la collection ChromaDB avec le bon modèle d'embeddings"""
    client = get_chroma_client()
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.get_or_create_collection(
        name='pei_documents',
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )


def extract_text_from_pdf(file_path):
    """Extrait le texte d'un PDF page par page"""
    try:
        doc = fitz.open(file_path)
        pages = []
        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            if text:  # Ignorer les pages vides
                pages.append({
                    'page': page_num + 1,
                    'text': text
                })
        doc.close()
        return pages
    except Exception as e:
        print(f"Erreur extraction PDF: {e}")
        return []


def chunk_text(text, chunk_size=500, overlap=50):
    """Découpe le texte en morceaux avec chevauchement"""
    words  = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def index_document(document):
    """
    Indexe un document Django dans ChromaDB.
    Retourne le nombre de chunks créés.
    """
    from .models import DocumentIndex

    # Vérifier si déjà indexé
    if DocumentIndex.objects.filter(document=document).exists():
        print(f"Document déjà indexé: {document.title}")
        return 0

    file_path = document.file_doc.path
    if not os.path.exists(file_path):
        print(f"Fichier introuvable: {file_path}")
        return 0

    # Extraire le texte
    pages = extract_text_from_pdf(file_path)
    if not pages:
        print(f"Aucun texte extrait de: {document.title}")
        return 0

    collection = get_collection()
    chunk_count = 0

    for page_data in pages:
        chunks = chunk_text(page_data['text'])
        for chunk_idx, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Ignorer les chunks trop courts
                continue

            chunk_id = f"doc_{document.id}_page_{page_data['page']}_chunk_{chunk_idx}"

            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{
                    'document_id':   str(document.id),
                    'document_title': document.title,
                    'subject':       document.subject.name,
                    'level':         document.subject.level.name,
                    'doc_type':      document.doc_type,
                    'page':          page_data['page'],
                }]
            )
            chunk_count += 1

    # Sauvegarder dans la BDD
    DocumentIndex.objects.create(
        document=document,
        chunk_count=chunk_count
    )

    print(f"Indexé: {document.title} — {chunk_count} chunks")
    return chunk_count


def search_documents(query, level_name=None, n_results=4):
    """
    Recherche les passages les plus pertinents pour une question.
    Filtre optionnel par année de l'étudiant.
    """
    try:
        collection = get_collection()

        # Construire le filtre par année si disponible
        where = None
        if level_name:
            where = {"level": {"$eq": level_name}}

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances']
        )

        passages = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                dist = results['distances'][0][i]

                # On garde seulement les résultats pertinents
                if dist < 1.2:
                    passages.append({
                        'text':    doc,
                        'title':   meta.get('document_title', ''),
                        'subject': meta.get('subject', ''),
                        'page':    meta.get('page', ''),
                        'score':   round(1 - dist, 2),
                    })

        return passages

    except Exception as e:
        print(f"Erreur recherche RAG: {e}")
        return []


def delete_document_index(document_id):
    """Supprime l'index d'un document de ChromaDB"""
    try:
        collection = get_collection()
        results = collection.get(
            where={"document_id": {"$eq": str(document_id)}}
        )
        if results['ids']:
            collection.delete(ids=results['ids'])
        print(f"Index supprimé pour document {document_id}")
    except Exception as e:
        print(f"Erreur suppression index: {e}")