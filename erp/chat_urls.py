from django.urls import path

from . import chat_views

urlpatterns = [
    path("", chat_views.mis_conversaciones, name="mis_conversaciones"),
    path("nueva/", chat_views.conversacion_nueva, name="conversacion_nueva"),
    path("<int:pk>/", chat_views.conversacion_detalle, name="conversacion_detalle"),
]

