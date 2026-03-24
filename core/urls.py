from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('library/', views.library, name='library'),
    path('account/', views.account, name='account'),
    path('profile/', views.profile, name='profile'),       # ← NOUVEAU
    path('tutor/', views.tutor, name='tutor'),             # ← manquait
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/search/', views.search_api, name='search_api'),
    path('logout/', views.custom_logout, name='logout'),
    path('tutor/clear/', views.clear_history, name='clear_history'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),        # ← NOUVEAU
    path('api/notifications/read/', views.mark_notifications_read, name='notifs_read'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/favoris/<int:doc_id>/', views.toggle_favori, name='toggle_favori'),
    path('favoris/', views.mes_favoris, name='favoris'),
]