import traceback
import base64
import json
import io
import time
from PIL import Image
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse

from .models import Conversation, Message
from projects.models import Project

# IMPORTAÇÕES DOS SEUS SERVIÇOS
from services.vision_service import analisar_imagem_qwen
from services.text_service import gerar_resposta_texto
from services.project_ai_service import gerar_resposta_projeto_codigo

def comprimir_imagem_para_ia(imagem_upload):
    """Comprime a imagem para não estourar o limite da API."""
    img = Image.open(imagem_upload)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail((800, 800))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def chat_view(request, id):
    conversation = get_object_or_404(Conversation, id=id)
    
    if request.method == 'POST':
        try:
            texto_usuario = request.POST.get('content', '').strip()
            imagens = request.FILES.getlist('images')

            # Se não enviou nada, ignora
            if not texto_usuario and not imagens:
                return JsonResponse({'status': 'erro', 'mensagem': 'Mensagem vazia.'})

            # Salva a mensagem do usuário no banco
            Message.objects.create(conversation=conversation, role='user', content=texto_usuario)
            
            # AUTO-DESCRIÇÃO E NOMEAÇÃO DO PROJETO
            if not conversation.project.description and texto_usuario:
                conversation.project.description = texto_usuario[:120] + "..."
                conversation.project.save()
            
            if conversation.title == "Chat Principal" or conversation.title.startswith("Nova"):
                conversation.title = texto_usuario[:30] + "..."
                conversation.save()

            tipo = conversation.project.tipo
            resposta_final_ia = ""

            # ==========================================
            # FLUXO 1: BANCADA DE ELETRÔNICA
            # ==========================================
            if tipo == 'eletronica':
                dados_visao = None
                
                # Passo A: Se tiver imagem, o JS no celular já criou um Mosaico e enviou apenas 1 imagem perfeita!
                if imagens:
                    img_b64 = comprimir_imagem_para_ia(imagens[0])
                    dados_visao = analisar_imagem_qwen(img_b64)
                
                # Passo B: IA de Texto assume como Professora de Eletrônica
                resposta_final_ia = gerar_resposta_texto(
                    dados_visao=dados_visao, 
                    texto_usuario=texto_usuario, 
                    tipo_projeto='eletronica'
                )

            # ==========================================
            # FLUXO 2: ESTÚDIO DE PROGRAMAÇÃO (O NOVO FLUXO INTELIGENTE)
            # ==========================================
            elif tipo == 'programacao':
                # Passo 1: Monta o histórico
                historico = ""
                for msg in conversation.messages.all().order_by('created_at'):
                    if msg.content:
                        historico += f"[{msg.role.upper()}]: {msg.content}\n"

                # Passo 2: Deixa a Professora conversar, estruturar e avaliar o pedido
                contexto_historico = f"HISTÓRICO DA CONVERSA PARA REFERÊNCIA:\n{historico}"
                resposta_professora = gerar_resposta_texto(
                    dados_visao=contexto_historico,
                    texto_usuario=texto_usuario,
                    tipo_projeto='programacao'
                )

                # Passo 3: O Sistema verifica se a Professora apertou o "Botão" de gerar código
                if "[GERAR_CODIGO]" in resposta_professora:
                    print("⚙️ [Sistema] A Professora autorizou a codificação! Acionando Programador...")
                    
                    # Limpa a tag para ela não aparecer na tela do usuário
                    resposta_professora = resposta_professora.replace("[GERAR_CODIGO]", "").strip()

                    # Aciona a IA de Código passando tudo o que a Professora estruturou!
                    codigo_puro = gerar_resposta_projeto_codigo(
                        historico_conversa=historico + f"\n[ESTRUTURA DEFINIDA PELA PROFESSORA]: {resposta_professora}\n",
                        projeto_nome=conversation.project.name,
                        projeto_descricao=conversation.project.description,
                        texto_usuario="A estrutura foi definida. Pode escrever todo o código do projeto."
                    )

                    time.sleep(4) # Pausa respiratória anti-bloqueio

                    # Devolve o Código para a Professora criar o Tutorial
                    contexto_tutorial = f"CÓDIGO GERADO PELO PROGRAMADOR NOS BASTIDORES:\n\n{codigo_puro}\n\nFaça o tutorial ensinando como usar, rodar e adaptar esse código."
                    tutorial_final = gerar_resposta_texto(
                        dados_visao=contexto_tutorial, 
                        texto_usuario="Aqui está o código gerado. Escreva o tutorial para o usuário.",
                        tipo_projeto='programacao'
                    )

                    # Junta o comentário de aprovação dela + Tutorial + Código
                    resposta_final_ia = f"""
                    <div style="margin-bottom: 20px;">{resposta_professora}</div>
                    {tutorial_final}
                    <div style="margin-top: 25px; padding-top: 15px; border-top: 1px dashed rgba(155,48,255,0.4);">
                        <h4 style="color: #DDA0DD; margin-bottom: 10px;">💻 Código do Projeto Gerado:</h4>
                        {codigo_puro}
                    </div>
                    """
                else:
                    # Se não tiver a tag, significa que eles ainda estão planejando a ideia! Retorna só a fala dela.
                    resposta_final_ia = resposta_professora

            # ==========================================
            # SALVA E RETORNA A MENSAGEM DA IA
            # ==========================================
            if resposta_final_ia and "Erro no servidor" not in resposta_final_ia:
                Message.objects.create(conversation=conversation, role='ai', content=resposta_final_ia)
                return JsonResponse({'status': 'sucesso', 'resposta_html': resposta_final_ia})
            else:
                # SE O OPENROUTER LIMITAR A TAXA, DESENHA O AVISO NO CHAT
                alerta_erro = """
                <div style="background: rgba(255, 68, 68, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #FF4444; margin-top: 10px;">
                    <h4 style="margin-top: 0; color: #FF4444;">⚠️ Instabilidade ou Limite de Taxa (OpenRouter)</h4>
                    <p style="color: #E0E0E0; font-size: 0.95rem;">As IAs gratuitas limitaram o nosso acesso temporariamente. Não se preocupe, <b>sua mensagem foi salva no histórico.</b></p>
                    <p style="color: #E0E0E0; font-size: 0.95rem;"><b>Como resolver:</b> Aguarde uns 10 segundos e envie <i>"continue"</i>. O sistema buscará outra IA do rodízio livre!</p>
                </div>
                """
                return JsonResponse({'status': 'erro', 'resposta_html': alerta_erro})

        except Exception as e:
            # SE O CÓDIGO PYTHON TRAVAR, O ERRO APARECE DIRETO NA TELA DO CHAT!
            erro_real = traceback.format_exc()
            print("\n================ ERRO FATAL NO CHAT ================")
            print(erro_real)
            print("====================================================\n")
            
            alerta_fatal = f"""
            <div style="background: rgba(255, 68, 68, 0.1); padding: 15px; border-radius: 8px; border: 1px solid #FF4444; margin-top: 10px;">
                <h4 style="margin-top: 0; color: #FF4444;">❌ Erro Crítico no Backend</h4>
                <p style="color: #E0E0E0; font-size: 0.95rem;">Ocorreu uma falha no sistema Django. Veja o detalhe abaixo ou olhe o terminal:</p>
                <pre style="background: #121218; padding: 10px; border-radius: 6px; color: #FF4444; font-size: 0.8rem; overflow-x: auto;">{str(e)}</pre>
            </div>
            """
            return JsonResponse({'status': 'erro', 'resposta_html': alerta_fatal})

    # SE FOR ACESSO NORMAL DA TELA (GET)
    messages = conversation.messages.all().order_by('created_at')
    return render(request, 'chat/conversation.html', {
        'conversation': conversation,
        'messages': messages
    })

# ==========================================
# OUTRAS VIEWS MANTIDAS
# ==========================================

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

def config_view(request):
    return render(request, 'config.html')

def home_view(request):
    return render(request, 'home.html')