from django.urls import path
from . import views 

urlpatterns=[
  path('',views.home,name='home'),
  path('library/',views.library,name='library'),
  path('account/',views.account,name='account'),
  path('api/chat/', views.chat_api, name='chat_api'),
  
]