from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
import json
import ollama 

# Create your views here.

def home(request):
  return render(request,"index.html")

def library(request):
  return render(request,"library.html")

@login_required
def account(request):
  return render(request,"account.html")


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
        history = request.session.get('chat_history', [
            {"role": "system", "content": SYSTEM_MESSAGE}
        ])

        # On ajoute le message de l'utilisateur
        history.append({"role": "user", "content": user_message})

        # Appel à Ollama (modèle llava:7b de ton script)
        response = ollama.chat(
            model="llava:7b",
            messages=history
        )
        
        assistant_message = response['message']['content']

        # On sauvegarde la réponse de l'IA dans l'historique pour la mémoire
        history.append({"role": "assistant", "content": assistant_message})
        request.session['chat_history'] = history

        return JsonResponse({"reply": assistant_message}) 