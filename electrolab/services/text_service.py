import os
import requests
from projects.models import UserTool

def obter_modelos_texto_gratuitos():
    try:
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

def gerar_resposta_texto(dados_visao, texto_usuario, tipo_projeto="eletronica"):
    api_key = os.environ.get("OPENROUTER_API_KEY")

    try:
        ferramentas_usuario = list(UserTool.objects.filter(disponivel=True).values_list('nome_ferramenta', flat=True))
        ferramentas_ausentes = list(UserTool.objects.filter(disponivel=False).values_list('nome_ferramenta', flat=True))
    except:
        ferramentas_usuario = []
        ferramentas_ausentes = []

    modelos_texto = obter_modelos_texto_gratuitos()

    if tipo_projeto == "programacao":
        papel = "Arquiteta de Software Sênior, Mentora e Professora de Programação."
        diretrizes = """
        1. Você é a Líder do Projeto. Sua primeira função é DEBATER E PLANEJAR (design, arquitetura, linguagens, banco de dados, ideias) junto com o usuário ANTES de codificar.
        2. Enquanto estiver na fase de planejamento, NÃO gere códigos completos. Aja como um consultor sênior orientando o usuário.
        3. SE O USUÁRIO INDICAR QUE A IDEIA ESTÁ PRONTA OU PEDIR PARA GERAR/ESCREVER O CÓDIGO FINAL, você DEVE escrever EXATAMENTE a tag [GERAR_CODIGO] no final da sua resposta. Essa tag aciona nosso robô programador nos bastidores.
        4. Se nos 'DADOS DE CONTEXTO' abaixo já houver um 'CÓDIGO GERADO PELO PROGRAMADOR', sua missão muda: escreva um tutorial didático ensinando o usuário a instalar, rodar e entender o código. NUNCA coloque a tag [GERAR_CODIGO] neste caso.
        """
    else:
        papel = "Engenheira Sênior, Especialista em Reparos Eletrônicos, Componentes e Professora de Bancada."
        diretrizes = f"""
        1. Escreva parágrafos explicativos, contexto técnico e princípios de funcionamento.
        2. Se for um reparo, forneça um guia de desmontagem minucioso, alertando sobre choques e uso de ferramentas.
        3. Considere as ferramentas da bancada. Possui: {ferramentas_usuario}. Faltam: {ferramentas_ausentes}. Nunca sugira usar o que ele não tem.
        """

    prompt_completo = f"""Você é a IA principal do ElectroLab: {papel}
    
    DIRETRIZES:
    {diretrizes}
    
    REGRA: Formate tudo em HTML limpo e elegante (<b>, <br>, <ul>, <li>, <h3>, <p>, <pre><code>). NUNCA use Markdown (**).
    
    DADOS DE CONTEXTO: 
    {dados_visao}
    
    COMANDO DO USUÁRIO: 
    {texto_usuario if texto_usuario else 'Vamos continuar.'}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for modelo in modelos_texto:
        try:
            print(f"🧠 [Professora IA - {tipo_projeto.upper()}] Pensando com {modelo}...")
            payload = {
                "model": modelo,
                "messages": [{"role": "user", "content": prompt_completo}],
                "max_tokens": 2000
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
            
            if response.status_code == 200:
                resposta_html = response.json()['choices'][0]['message']['content'].strip()
                if resposta_html.startswith('```html'): resposta_html = resposta_html[7:]
                if resposta_html.startswith('```'): resposta_html = resposta_html[3:]
                if resposta_html.endswith('```'): resposta_html = resposta_html[:-3]
                
                return resposta_html.strip()
        except Exception:
            continue
            
    return "<b>Erro no servidor:</b> Falha na IA de Texto/Professor."