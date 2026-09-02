import os
import requests
from projects.models import UserTool

def obter_modelos_texto_gratuitos():
    """Busca dinamicamente modelos de texto gratuitos no OpenRouter."""
    try:
        print("🔍 Buscando IAs de texto gratuitas hoje...")
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        
        if response.status_code == 200:
            modelos = response.json().get("data", [])
            modelos_validos = []
            
            for m in modelos:
                pricing = m.get("pricing", {})
                if str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0":
                    id_modelo = m.get("id", "").lower()
                    if "safety" not in id_modelo and "moderation" not in id_modelo:
                        modelos_validos.append(m["id"])
            
            if "openrouter/free" not in modelos_validos:
                modelos_validos.append("openrouter/free")
                
            return modelos_validos[:4]
    except:
        pass
    
    return ["openrouter/free"]

def gerar_resposta_texto(dados_visao, texto_usuario):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    # Pega as ferramentas cadastradas pelo usuário no banco de dados
    try:
        ferramentas_usuario = list(UserTool.objects.filter(disponivel=True).values_list('nome_ferramenta', flat=True))
        ferramentas_ausentes = list(UserTool.objects.filter(disponivel=False).values_list('nome_ferramenta', flat=True))
    except:
        ferramentas_usuario = []
        ferramentas_ausentes = []

    modelos_texto = obter_modelos_texto_gratuitos()

    prompt_completo = f"""Você é a IA principal do ElectroLab, um Engenheiro Sênior e Especialista em Reparos.
    Sua missão é ler os DADOS DA IMAGEM e o COMANDO DO USUÁRIO e entregar uma resposta profunda, rica e continuável.
    
    RESTRIÇÕES DE BANCADA DO USUÁRIO:
    - Ferramentas que ele POSSUI e pode usar: {ferramentas_usuario if ferramentas_usuario else 'Nenhuma cadastrada, assumir padrão básico'}
    - Ferramentas que ele NÃO POSSUI: {ferramentas_ausentes if ferramentas_ausentes else 'Nenhuma'}
    (ATENÇÃO: É ESTRITAMENTE PROIBIDO sugerir ou orientar o uso de qualquer ferramenta que esteja na lista de ausentes).

    DIRETRIZES DE EXCELÊNCIA:
    1. Não faça apenas listas. Escreva parágrafos explicativos, contexto técnico, princípios de funcionamento e possíveis adaptações ou usos alternativos (hacks).
    2. Se for um reparo, forneça um guia de desmontagem minucioso, alertando sobre travas sensíveis, riscos de choque elétrico e apenas com as ferramentas disponíveis.
    3. Deixe ganchos para que o usuário possa continuar a conversa (ex: "Se quiser, posso detalhar como testar o componente X").
    4. Formate tudo em HTML limpo e elegante (<b>, <br>, <ul>, <li>, <h3>, <p>). NUNCA use Markdown (**).
    
    DADOS DA IMAGEM: 
    {dados_visao}
    
    COMANDO DO USUÁRIO: 
    {texto_usuario if texto_usuario else 'Faça uma análise técnica profunda, guia de desmontagem e possíveis usos para este equipamento.'}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for modelo in modelos_texto:
        try:
            print(f"🧠 [IA de Texto] Pensando com {modelo}...")
            payload = {
                "model": modelo,
                "messages": [
                    {"role": "user", "content": prompt_completo}
                ],
                "max_tokens": 2000
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
            
            if response.status_code == 200:
                resposta_html = response.json()['choices'][0]['message']['content'].strip()
                
                if resposta_html.startswith('```html'): resposta_html = resposta_html[7:]
                if resposta_html.startswith('```'): resposta_html = resposta_html[3:]
                if resposta_html.endswith('```'): resposta_html = resposta_html[:-3]
                
                print(f"✅ IA de Texto formatou a resposta com sucesso!")
                return resposta_html.strip()
            else:
                continue
                
        except Exception as e:
            continue
            
    return "<b>Erro no servidor:</b> Não foi possível formatar a resposta da IA de texto no momento."