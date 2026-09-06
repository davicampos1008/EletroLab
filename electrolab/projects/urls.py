from django.urls import path
from . import views

urlpatterns = [
    # -----------------------------------------
    # ROTAS DE PROJETOS (Eletrônica e Código)
    # -----------------------------------------
    path('eletronica/', views.lista_eletronica, name='list_electronics'),
    path('programacao/', views.lista_programacao, name='list_programming'),
    path('novo/', views.project_create, name='project_create'),
    
    # -----------------------------------------
    # ROTAS DE AÇÃO (Abrir Chat e Excluir)
    # -----------------------------------------
    path('<int:project_id>/abrir/', views.open_project_chat, name='project_chat'),
    path('<int:project_id>/excluir/', views.project_delete, name='project_delete'),
    
    # -----------------------------------------
    # ROTAS DE INVENTÁRIO, SCAN E GARIMPO
    # -----------------------------------------
    path('garimpo/', views.scout_item_view, name='scout_item_view'),
    path('scan/', views.scan_inventory_view, name='scan_inventory_view'),
    path('estoque/', views.inventory_list_view, name='inventory_list_view'),
    path('salvar-estoque/', views.save_inventory_batch, name='save_inventory_batch'),
]