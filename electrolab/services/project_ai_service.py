import os
import requests

def obter_modelos_texto_gratuitos():
    """Busca dinamicamente modelos de texto gratuitos no OpenRouter."""
    try:
        response = requests.get("[https://openrouter.ai/api/v1/models](https://openrouter.ai/api/v1/models)", timeout=10)
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

def gerar_resposta_projeto_codigo(historico_conversa, projeto_nome, projeto_descricao, texto_usuario):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    modelos_texto = obter_modelos_texto_gratuitos()

    # O PROMPT FOCADO APENAS EM PROGRAMAÇÃO DE ALTO NÍVEL
    prompt_completo = f"""Você é o "Agente Programador Mestre" do ElectroLab. 
    Sua ÚNICA missão é escrever códigos perfeitos, completos e livres de bugs. Outra IA cuidará de explicar o código ao usuário.

    CONTEXTO DO PROJETO:
    - Nome do Projeto: {projeto_nome}
    - Descrição: {projeto_descricao if projeto_descricao else 'Identifique a linguagem pelo pedido abaixo.'}
    
    HISTÓRICO ANTERIOR PARA MANTER A CONSISTÊNCIA DAS VARIÁVEIS E LÓGICA:
    {historico_conversa}

    PEDIDO ATUAL DO USUÁRIO: 
    {texto_usuario}

    REGRAS ESTRITAS DE CODIFICAÇÃO:
    1. Retorne APENAS o código bruto, formatado em HTML seguro usando a tag <pre><code> ... </code></pre>. 
    2. NÃO escreva introduções como "Aqui está o código" e NENHUMA explicação final. Apenas o <pre><code>.
    3. O código DEVE SER COMPLETO. Nunca escreva comentários preguiçosos como "// Insira a lógica aqui". Escreva a lógica real.
    4. Siga as melhores práticas da linguagem solicitada (ou inferida), incluindo tratamento de erros e segurança.
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for modelo in modelos_texto:
        try:
            print(f"🧠 [Agente Programador] Escrevendo código com {modelo}...")
            payload = {
                "model": modelo,
                "messages": [{"role": "user", "content": prompt_completo}],
                "max_tokens": 3000 # Maximo possível para códigos longos
            }
            
            response = requests.post("[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)", headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                codigo_html = response.json()['choices'][0]['message']['content'].strip()
                # Limpa marcações indesejadas caso a IA teimosamente use markdown
                if codigo_html.startswith('```html'): codigo_html = codigo_html[7:]
                if codigo_html.startswith('```'): codigo_html = codigo_html[3:]
                if codigo_html.endswith('```'): codigo_html = codigo_html[:-3]
                
                return codigo_html.strip()
        except Exception:
            continue
            
    return "<pre><code>// Erro no servidor: Não foi possível gerar o código.</code></pre>"