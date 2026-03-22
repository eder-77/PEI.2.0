from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Document,Level,Subject
from django.http import JsonResponse
import json
import ollama
from django.db.models import Q
from django.http import JsonResponse

# Create your views here.


def home(request):
    return render(request, "index.html")


# Fichier : core/views.py
from django.shortcuts import render
from .models import Document, Level, Subject


def library(request):
    # la barre de recherche:
    search_query = request.GET.get("q", "").strip()

    if search_query:
        documents = Document.objects.filter(
            Q(title__icontains=search_query) | Q(subject__name__icontains=search_query)
        ).order_by('-uploaded_at')

        return render(
            request, 'library.html', 
            {
            'step': 'search_results',
            'documents': documents,
            'search_query': search_query,
        })    

        
    
     
    # On regarde si l'URL contient des paramètres (ex: ?level=1&subject=2&type=COUR)
    level_id = request.GET.get("level")
    subject_id = request.GET.get("subject")
    doc_type = request.GET.get("type")

    # ÉTAPE 4 : On a cliqué sur un Type (On affiche les PDF finaux)
    if level_id and subject_id and doc_type:
        documents = Document.objects.filter(
            subject_id=subject_id, doc_type=doc_type
        ).order_by("-uploaded_at")
        current_subject = Subject.objects.get(id=subject_id)

        # On trouve le nom lisible du type (ex: "Travaux Pratiques" au lieu de "TP")
        type_name = dict(Document.TYPE_CHOICES).get(doc_type)

        return render(
            request,
            "library.html",
            {
                "step": "files",
                "documents": documents,
                "current_subject": current_subject,
                "type_name": type_name,
                "level_id": level_id,
            },
        )
    

    # ÉTAPE 3 : On a cliqué sur un Module (On affiche les 3 dossiers : Cours, TP, Examens)
    elif level_id and subject_id:
        current_subject = Subject.objects.get(id=subject_id)
        # On récupère les choix définis dans models.py (COUR, TP, EXAM)
        types = Document.TYPE_CHOICES
        return render(
            request,
            "library.html",
            {
                "step": "types",
                "types": types,
                "current_subject": current_subject,
                "level_id": level_id,
            },
        )

    # ÉTAPE 2 : On a cliqué sur une Année (On affiche les Modules de cette année)
    elif level_id:
        current_level = Level.objects.get(id=level_id)
        subjects = Subject.objects.filter(level=current_level)
        return render(
            request,
            "library.html",
            {"step": "subjects", "subjects": subjects, "current_level": current_level},
        )

    # ÉTAPE 1 : Par défaut, quand on arrive sur la page (On affiche les Années)
    else:
        levels = Level.objects.all()

        return render(request, "library.html", {"step": "levels", "levels": levels})


@login_required
def account(request):
    return render(request, "account.html")


# On reprend les réglages de ton script rag.py
SYSTEM_MESSAGE = """Tu es un assistant universitaire expert en algorithmes et programmation.
Tes objectifs:
- Expliquer clairement et de manière pédagogique
- Fournir du code C complet avec commentaires si nécessaire
- Répondre de façon concise mais complète
- Être patient et encourageant avec les étudiants"""


def chat_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")

        # On récupère l'historique ou on initialise avec le message système
        history = request.session.get(
            "chat_history", [{"role": "system", "content": SYSTEM_MESSAGE}]
        )

        # On ajoute le message de l'utilisateur
        history.append({"role": "user", "content": user_message})

        # Appel à Ollama (modèle llava:7b de ton script)
        response = ollama.chat(model="llava:7b", messages=history)

        assistant_message = response["message"]["content"]

        # On sauvegarde la réponse de l'IA dans l'historique pour la mémoire
        history.append({"role": "assistant", "content": assistant_message})
        request.session["chat_history"] = history

        return JsonResponse({"reply": assistant_message})
    
def search_api(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    results = []

    # 1. Chercher dans les DOCUMENTS (titres)
    documents = Document.objects.filter(
        title__icontains=query
    ).select_related('subject__level')[:8]

    for doc in documents:
        results.append({
            'type': 'document',
            'id': doc.id,
            'title': doc.title,
            'subject': doc.subject.name,
            'level': doc.subject.level.get_name_display(),
            'level_id': doc.subject.level.id,
            'subject_id': doc.subject.id,
            'doc_type': doc.get_doc_type_display(),
            'doc_type_code': doc.doc_type,
            'file_url': doc.file_doc.url if doc.file_doc else None,
            'date': doc.uploaded_at.strftime('%d/%m/%Y'),
            # URL directe vers le dossier de ce document dans la navigation
            'nav_url': f'/library/?level={doc.subject.level.id}&subject={doc.subject.id}&type={doc.doc_type}',
        })

    # 2. Chercher dans les MATIÈRES (modules)
    subjects = Subject.objects.filter(
        name__icontains=query
    ).select_related('level')[:5]

    for subject in subjects:
        results.append({
            'type': 'subject',
            'title': subject.name,
            'subtitle': subject.level.get_name_display(),
            'nav_url': f'/library/?level={subject.level.id}&subject={subject.id}',
        })

    # 3. Chercher dans les ANNÉES
    levels = Level.objects.filter(
        name__icontains=query
    )[:3]

    for level in levels:
        results.append({
            'type': 'level',
            'title': level.get_name_display(),
            'subtitle': 'Année d\'étude',
            'nav_url': f'/library/?level={level.id}',
        })

    return JsonResponse({'results': results, 'count': len(results)})
