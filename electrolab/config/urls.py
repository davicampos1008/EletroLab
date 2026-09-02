from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from chat.views import config_view, home_view
from projects.views import (
    scan_inventory_view, 
    inventory_list_view, 
    save_inventory_batch, 
    scout_item_view  # <-- Certifique-se de importar esta view aqui
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home_view'),
    path('projetos/', include('projects.urls')),
    path('chat/', include('chat.urls')),
    path('configuracoes/', config_view, name='config_view'),
    
    # Rotas do Inventário e Garimpo
    path('estoque/scan/', scan_inventory_view, name='scan_inventory_view'),
    path('estoque/pecas/', inventory_list_view, name='inventory_list_view'),
    path('estoque/salvar-lote/', save_inventory_batch, name='save_inventory_batch'),
    path('garimpo/', scout_item_view, name='scout_item_view'), # <-- Nova rota do radar de sucata
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)