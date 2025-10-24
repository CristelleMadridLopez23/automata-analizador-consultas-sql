from django.urls import path
from .views import index

# Rutas de la app de análisis léxico.
# Define la vista principal `index` en la raíz de la app.

urlpatterns = [
    path("", index, name="sql_index"),
]
