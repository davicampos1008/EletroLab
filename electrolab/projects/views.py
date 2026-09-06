from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import base64
import io
from PIL import Image

# Modelos
from .models import Project, InventoryItem
from chat.models import Conversation, Message

# Seus serviços de IA para Inventário e Garimpo
from services.inventory_service import analisar_pecas_para_estoque
from services.scout_service import analisar_garimpo_sucata

# ==========================================
# 1. LISTAS SEPARADAS DE PROJETOS
# ==========================================
def lista_eletronica(request):
    projetos = Project.objects.filter(tipo='eletronica').order_by('-created_at')
    return render(request, 'projects/list_electronics.html', {'projects': projetos})

def lista_programacao(request):
    projetos = Project.objects.filter(tipo='programacao').order_by('-created_at')
    return render(request, 'projects/list_programming.html', {'projects': projetos})

# ==========================================
# 2. CRIAÇÃO, ABERTURA E EXCLUSÃO DE PROJETOS
# ==========================================
def project_create(request):
    tipo_projeto = request.GET.get('tipo', 'eletronica')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        tipo_post = request.POST.get('tipo', tipo_projeto)
        
        if name:
            project = Project.objects.create(name=name, description=description, tipo=tipo_post)
            # Cria a conversa principal e redireciona direto para o chat
            conversation = Conversation.objects.create(project=project, title="Chat Principal")
            return redirect('conversation', conversation.id)
            
    if tipo_projeto == 'programacao':
        return render(request, 'projects/create_programming.html', {'tipo': tipo_projeto})
    else:
        return render(request, 'projects/create_electronics.html', {'tipo': tipo_projeto})

def open_project_chat(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    conversation = project.conversations.first()
    
    if not conversation:
        conversation = Conversation.objects.create(project=project, title="Chat Principal")
        
    return redirect('conversation', conversation.id)

def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tipo = project.tipo
    
    # Exclui o projeto e todas as conversas/mensagens atreladas
    project.delete()
    
    if tipo == 'programacao':
        return redirect('list_programming')
    return redirect('list_electronics')

# ==========================================
# 3. GARIMPO, ESTOQUE E FERRAMENTAS
# ==========================================
def scout_item_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        imagens = request.FILES.getlist('images')
        if imagens:
            base64_lista = []
            for img in imagens:
                base64_encoded = comprimir_imagem_para_ia(img)
                base64_lista.append(base64_encoded)
                
            dados_garimpo = analisar_garimpo_sucata(base64_lista)
            return JsonResponse({'status': 'sucesso', 'dados': dados_garimpo})
            
        return JsonResponse({'status': 'erro', 'mensagem': 'Nenhuma imagem enviada'})
    
    return render(request, 'inventory/scout.html')

def scan_inventory_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        imagem = request.FILES.get('image')
        if imagem:
            base64_encoded = comprimir_imagem_para_ia(imagem)
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

def comprimir_imagem_para_ia(imagem_upload):
    img = Image.open(imagem_upload)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail((800, 800))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')