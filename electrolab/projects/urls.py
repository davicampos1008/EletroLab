from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import InventoryItem
from services.inventory_service import analisar_pecas_para_estoque
import base64
from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('novo/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
]

def scan_inventory_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        imagem = request.FILES.get('image')
        if imagem:
            image_bytes = imagem.read()
            base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
            dados_pecas = analisar_pecas_para_estoque(base64_encoded)
            return JsonResponse({'status': 'sucesso', 'dados': dados_pecas})
        return JsonResponse({'status': 'erro', 'mensagem': 'Nenhuma imagem enviada'})
    
    return render(request, 'inventory/scan.html')

def inventory_list_view(request):
    items = InventoryItem.objects.all().order_by('-criado_em')
    return render(request, 'inventory/list.html', {'items': items})

def save_inventory_batch(request):
    if request.method == 'POST':
        origem = request.POST.get('equipamento_origem', 'Desconhecido')
        
        # Varre os dados enviados via POST pelo formulário em lote
        key_list = list(request.POST.keys())
        for key in key_list:
            if key.startswith('peca_nome_'):
                index = key.split('_')[-1]
                nome = request.POST.get(f'peca_nome_{index}')
                desc = request.POST.get(f'peca_desc_{index}')
                qtd = request.POST.get(f'peca_qtd_{index}', 1)
                
                if nome:
                    InventoryItem.objects.create(
                        nome=nome,
                        descricao=desc,
                        quantidade=int(qtd),
                        origem_equipamento=origem
                    )
        return redirect('inventory_list_view')
    return redirect('scan_inventory_view')