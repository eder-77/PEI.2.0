from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Document, Level, Subject, StudentProfile, ChatMessage, Notification,Favori
from django.http import JsonResponse
import json
import ollama
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta


# Create your views here.


def home(request):
    if request.user.is_authenticated:
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)

        # Si l'étudiant a choisi son année, on filtre par son année
        if profile.year:
            level = Level.objects.filter(name=profile.year).first()

            total_docs = Document.objects.filter(subject__level=level).count()
            total_subjects = Subject.objects.filter(level=level).count()
            total_exams = Document.objects.filter(
                subject__level=level, doc_type="EXAM"
            ).count()
            total_tp = Document.objects.filter(
                subject__level=level, doc_type="TP"
            ).count()

            recent_docs = (
                Document.objects.filter(subject__level=level)
                .select_related("subject__level")
                .order_by("-uploaded_at")[:5]
            )

            niveau_label = level.get_name_display()

        # Sinon on affiche tout (étudiant sans année choisie)
        else:
            total_docs = Document.objects.count()
            total_subjects = Subject.objects.count()
            total_exams = Document.objects.filter(doc_type="EXAM").count()
            total_tp = Document.objects.filter(doc_type="TP").count()
            recent_docs = Document.objects.select_related("subject__level").order_by(
                "-uploaded_at"
            )[:5]
            niveau_label = None

        return render(
            request,
            "index.html",
            {
                "profile": profile,
                "total_docs": total_docs,
                "total_subjects": total_subjects,
                "total_exams": total_exams,
                "total_tp": total_tp,
                "recent_docs": recent_docs,
                "niveau_label": niveau_label,
            },
        )

    return render(request, "index.html")


def library(request):
    # la barre de recherche:
    search_query = request.GET.get("q", "").strip()

    if search_query:
        documents = Document.objects.filter(
            Q(title__icontains=search_query) | Q(subject__name__icontains=search_query)
        ).order_by("-uploaded_at")

        return render(
            request,
            "library.html",
            {
                "step": "search_results",
                "documents": documents,
                "search_query": search_query,
            },
        )

    # On regarde si l'URL contient des paramètres (ex: ?level=1&subject=2&type=COUR)
    level_id = request.GET.get("level")
    subject_id = request.GET.get("subject")
    doc_type = request.GET.get("type")

    # ÉTAPE 4 : On a cliqué sur un Type (On affiche les PDF finaux)
    if level_id and subject_id and doc_type:
      documents = Document.objects.filter(
        subject_id=subject_id, doc_type=doc_type
      ).order_by('-uploaded_at')
      current_subject = Subject.objects.get(id=subject_id)
      type_name = dict(Document.TYPE_CHOICES).get(doc_type)

    # IDs des favoris de l'utilisateur connecté
      fav_ids = []
      if request.user.is_authenticated:
          fav_ids = list(
              Favori.objects.filter(user=request.user).values_list('document_id', flat=True)
          )

      return render(request, 'library.html', {
          'step':            'files',
          'documents':       documents,
          'current_subject': current_subject,
          'type_name':       type_name,
          'level_id':        level_id,
          'fav_ids':         fav_ids,
      })

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
    return redirect("profile")


# On reprend les réglages de ton script rag.py
SYSTEM_MESSAGE = """Tu es un assistant universitaire expert en algorithmes et programmation.
Tes objectifs:
- Expliquer clairement et de manière pédagogique
- Fournir du code C complet avec commentaires si nécessaire
- Répondre de façon concise mais complète
- Être patient et encourageant avec les étudiants"""


@login_required
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"error": "Message vide"}, status=400)

            # Sauvegarder le message utilisateur en base de données
            ChatMessage.objects.create(
                user=request.user, role="user", content=user_message
            )

            # Construire l'historique pour Ollama (50 derniers messages)
            history = [{"role": "system", "content": SYSTEM_MESSAGE}]
            past_messages = ChatMessage.objects.filter(user=request.user).order_by(
                "created_at"
            )[:50]

            for msg in past_messages:
                history.append({"role": msg.role, "content": msg.content})

            # Appel à Ollama
            response = ollama.chat(model="llava:7b", messages=history)
            assistant_reply = response["message"]["content"]

            # Sauvegarder la réponse de l'IA en base de données
            ChatMessage.objects.create(
                user=request.user, role="assistant", content=assistant_reply
            )

            return JsonResponse({"reply": assistant_reply})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


def search_api(request):
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    results = []

    # 1. Chercher dans les DOCUMENTS (titres)
    documents = Document.objects.filter(title__icontains=query).select_related(
        "subject__level"
    )[:8]

    for doc in documents:
        results.append(
            {
                "type": "document",
                "id": doc.id,
                "title": doc.title,
                "subject": doc.subject.name,
                "level": doc.subject.level.get_name_display(),
                "level_id": doc.subject.level.id,
                "subject_id": doc.subject.id,
                "doc_type": doc.get_doc_type_display(),
                "doc_type_code": doc.doc_type,
                "file_url": doc.file_doc.url if doc.file_doc else None,
                "date": doc.uploaded_at.strftime("%d/%m/%Y"),
                # URL directe vers le dossier de ce document dans la navigation
                "nav_url": f"/library/?level={doc.subject.level.id}&subject={doc.subject.id}&type={doc.doc_type}",
            }
        )

    # 2. Chercher dans les MATIÈRES (modules)
    subjects = Subject.objects.filter(name__icontains=query).select_related("level")[:5]

    for subject in subjects:
        results.append(
            {
                "type": "subject",
                "title": subject.name,
                "subtitle": subject.level.get_name_display(),
                "nav_url": f"/library/?level={subject.level.id}&subject={subject.id}",
            }
        )

    # 3. Chercher dans les ANNÉES
    levels = Level.objects.filter(name__icontains=query)[:3]

    for level in levels:
        results.append(
            {
                "type": "level",
                "title": level.get_name_display(),
                "subtitle": "Année d'étude",
                "nav_url": f"/library/?level={level.id}",
            }
        )

    return JsonResponse({"results": results, "count": len(results)})


# ════════════════════════════════════════
# NOUVEAU : Tuteur (manquait dans urls.py)
# ════════════════════════════════════════
@login_required
def tutor(request):
    # Récupère les 50 derniers messages de l'utilisateur connecté
    messages_history = ChatMessage.objects.filter(user=request.user).order_by(
        "created_at"
    )[:50]

    return render(request, "tutor.html", {"messages_history": messages_history})


SYSTEM_MESSAGE = """Tu es un assistant universitaire expert en algorithmes et programmation.
Tes objectifs:
- Expliquer clairement et de manière pédagogique
- Fournir du code C complet avec commentaires si nécessaire
- Répondre de façon concise mais complète
- Être patient et encourageant avec les étudiants"""


@login_required
def clear_history(request):
    if request.method == "POST":
        ChatMessage.objects.filter(user=request.user).delete()
    return redirect("tutor")


# ════════════════════════════════════════
# NOUVEAU : Profil étudiant
# ════════════════════════════════════════


@login_required
def profile(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", "")
        request.user.last_name = request.POST.get("last_name", "")
        request.user.save()

        profile.year = request.POST.get("year", "")
        profile.bio = request.POST.get("bio", "")

        if "avatar" in request.FILES:
            profile.avatar = request.FILES["avatar"]

        profile.save()
        messages.success(request, "Profil mis à jour avec succès !")
        return redirect("profile")

    return render(
        request,
        "account.html",
        {
            "profile": profile,
            "year_choices": StudentProfile.YEAR_CHOICES,
        },
    )


def custom_logout(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")


@login_required
def mark_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
    return JsonResponse({"status": "ok"})


@login_required
def notifications_api(request):
    notifs = Notification.objects.filter(user=request.user).select_related(
        "document__subject__level"
    )[:10]

    data = []
    for n in notifs:
        data.append(
            {
                "id": n.id,
                "title": n.document.title,
                "subject": n.document.subject.name,
                "level": n.document.subject.level.get_name_display(),
                "type": n.document.get_doc_type_display(),
                "url": n.document.file_doc.url if n.document.file_doc else "#",
                "is_read": n.is_read,
                "date": n.created_at.strftime("%d/%m/%Y"),
            }
        )

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({"notifications": data, "unread": unread_count})


@staff_member_required
def dashboard(request):

    # ── Statistiques globales ──
    total_docs      = Document.objects.count()
    total_students  = User.objects.filter(is_staff=False).count()
    total_subjects  = Subject.objects.count()
    total_levels    = Level.objects.count()
    total_messages  = ChatMessage.objects.count()

    # ── Documents par type ──
    docs_cours = Document.objects.filter(doc_type='COURS').count()
    docs_tp    = Document.objects.filter(doc_type='TP').count()
    docs_exam  = Document.objects.filter(doc_type='EXAM').count()

    # ── Documents par année ──
    docs_par_niveau = []
    for level in Level.objects.all():
        count = Document.objects.filter(subject__level=level).count()
        docs_par_niveau.append({
            'level': level.get_name_display(),
            'count': count,
        })

    # ── Étudiants par année ──
    etudiants_par_niveau = []
    for level in Level.objects.all():
        count = StudentProfile.objects.filter(year=level.name).count()
        etudiants_par_niveau.append({
            'level': level.get_name_display(),
            'count': count,
        })

    # ── Derniers documents ajoutés ──
    recent_docs = Document.objects.select_related(
        'subject__level'
    ).order_by('-uploaded_at')[:8]

    # ── Derniers étudiants inscrits ──
    recent_students = User.objects.filter(
        is_staff=False
    ).order_by('-date_joined')[:5]

    # ── Activité des 7 derniers jours ──
    today = timezone.now()
    activite = []
    for i in range(6, -1, -1):
        day   = today - timedelta(days=i)
        label = day.strftime('%d/%m')
        count = Document.objects.filter(
            uploaded_at__date=day.date()
        ).count()
        activite.append({'day': label, 'count': count})

    return render(request, 'dashboard.html', {
        'total_docs':            total_docs,
        'total_students':        total_students,
        'total_subjects':        total_subjects,
        'total_levels':          total_levels,
        'total_messages':        total_messages,
        'docs_cours':            docs_cours,
        'docs_tp':               docs_tp,
        'docs_exam':             docs_exam,
        'docs_par_niveau':       docs_par_niveau,
        'etudiants_par_niveau':  etudiants_par_niveau,
        'recent_docs':           recent_docs,
        'recent_students':       recent_students,
        'activite':              activite,
    })


@login_required
def toggle_favori(request, doc_id):
    """Ajouter ou retirer un document des favoris"""
    if request.method == 'POST':
        doc    = Document.objects.get(id=doc_id)
        favori = Favori.objects.filter(user=request.user, document=doc)

        if favori.exists():
            favori.delete()
            is_fav = False
        else:
            Favori.objects.create(user=request.user, document=doc)
            is_fav = True

        return JsonResponse({'is_fav': is_fav})

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def mes_favoris(request):
    """Page listant tous les favoris de l'étudiant"""
    favoris = Favori.objects.filter(
        user=request.user
    ).select_related('document__subject__level')

    return render(request, 'favoris.html', {'favoris': favoris})