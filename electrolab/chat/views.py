import base64
import json
import io
from PIL import Image
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse

from .models import Conversation, Message
from projects.models import Project
from services.vision_service import analisar_imagem_qwen
from services.text_service import gerar_resposta_texto

import threading


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title', 'Nova Análise Tech')
        conversation = Conversation.objects.create(project=project, title=title)
        return redirect('conversation', id=conversation.id)
    
    conversations = project.conversations.all()
    context = {
        'project': project,
        'conversations': conversations,
    }
    return render(request, 'projects/detail.html', context)


def processar_ia_em_segundo_plano(conversation_id, texto, dados_visao):
    try:
        from .models import Conversation, Message
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Auto-nomeação inteligente baseada no conteúdo
        if conversation.title.startswith("Nova Análise") or conversation.title == "Nova Conversa" or conversation.title == "Nova Sessão Analítica":
            nome_inteligente = None
            if dados_visao:
                if dados_visao.get('is_tecnico'):
                    nome_inteligente = dados_visao.get('dados_tecnicos', {}).get('equipamento_ou_placa')
                else:
                    nome_inteligente = dados_visao.get('dados_gerais', {}).get('nome_objeto')
            
            if not nome_inteligente and texto:
                nome_inteligente = texto[:35]
            
            if nome_inteligente:
                conversation.title = nome_inteligente
                conversation.save()

        resposta_final = gerar_resposta_texto(dados_visao, texto)
        Message.objects.create(conversation=conversation, role='ai', content=resposta_final)
    except Exception as e:
        print(f"❌ [Background Thread] Erro: {str(e)}")


def comprimir_imagem_para_ia(imagem_file):
    img = Image.open(imagem_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def chat_view(request, id):
    conversation = get_object_or_404(Conversation, id=id)
    messages = conversation.messages.all() 

    if request.method == 'POST':
        step = request.POST.get('step')

        if step == 'vision':
            imagem = request.FILES.get('images')
            dados_extraidos = None
            if imagem:
                image_bytes_leves = comprimir_imagem_para_ia(imagem)
                base64_encoded = base64.b64encode(image_bytes_leves).decode('utf-8')
                dados_extraidos = analisar_imagem_qwen(base64_encoded)
                imagem.seek(0)
            return JsonResponse({'status': 'sucesso', 'dados_visao': dados_extraidos})

        if step == 'text':
            texto = request.POST.get('content', '') 
            dados_visao_str = request.POST.get('dados_visao', '')
            dados_visao = json.loads(dados_visao_str) if dados_visao_str else None

            Message.objects.create(conversation=conversation, role='user', content=texto)

            thread_ia = threading.Thread(
                target=processar_ia_em_segundo_plano, 
                args=(conversation.id, texto, dados_visao)
            )
            thread_ia.start()

            return JsonResponse({
                'status': 'processando', 
                'mensagem': 'A IA está formulando o relatório em segundo plano.'
            })

    context = {
        'conversation': conversation,
        'messages': messages,
    }
    return render(request, 'chat/conversation.html', context)


def config_view(request):
    return render(request, 'config.html')

def home_view(request):
    return render(request, 'home.html')