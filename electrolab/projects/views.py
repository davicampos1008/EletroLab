from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import InventoryItem
from services.inventory_service import analisar_pecas_para_estoque
import base64
from services.scout_service import analisar_garimpo_sucata


def project_list(request):
    projects = Project.objects.all().order_by('-updated_at')

    return render(request, 'projects/list.html', {
        'projects': projects
    })

def scout_item_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        imagem = request.FILES.get('image')
        if imagem:
            image_bytes = imagem.read()
            base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
            dados_garimpo = analisar_garimpo_sucata(base64_encoded)
            return JsonResponse({'status': 'sucesso', 'dados': dados_garimpo})
        return JsonResponse({'status': 'erro', 'mensagem': 'Nenhuma imagem enviada'})
    
    return render(request, 'inventory/scout.html')

def project_create(request):

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name:

            project = Project.objects.create(
                name=name,
                description=description
            )

            return redirect(
                'project_detail',
                project_id=project.id
            )

    return render(request, 'projects/create.html')


def project_detail(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id
    )

    conversations = project.conversations.all().order_by(
        '-updated_at'
    )

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()

        if title:

            conversation = Conversation.objects.create(
                project=project,
                title=title
            )

            return redirect(
                'conversation',
                conversation_id=conversation.id
            )

    return render(
        request,
        'projects/detail.html',
        {
            'project': project,
            'conversations': conversations
        }
    )

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