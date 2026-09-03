import os
import requests
import json

def obter_modelos_visao_gratuitos():
    """Busca na API do OpenRouter todos os modelos 100% gratuitos do dia que suportam visão."""
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if response.status_code == 200:
            modelos = response.json().get("data", [])
            modelos_validos = []
            
            for m in modelos:
                pricing = m.get("pricing", {})
                is_free = str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0"
                
                if is_free:
                    id_modelo = m.get("id", "").lower()
                    arch = m.get("architecture", {})
                    modality = arch.get("modality", "").lower()
                    
                    aceita_imagem = "image" in modality or "vision" in id_modelo or "vl" in id_modelo or "gemini" in id_modelo
                    is_seguranca = "safety" in id_modelo or "moderation" in id_modelo
                    
                    if aceita_imagem and not is_seguranca:
                        modelos_validos.append(m["id"])
            
            if "openrouter/free" not in modelos_validos:
                modelos_validos.append("openrouter/free")
                
            return modelos_validos
    except Exception:
        pass
    # Fallback super seguro se a busca falhar
    return ["google/gemini-2.0-flash-lite-preview-02-05:free", "google/gemini-2.0-pro-exp-02-05:free"]

def analisar_garimpo_sucata(base64_image):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    prompt = """Você é um especialista em engenharia de campo, reciclagem eletrônica e viabilidade de consertos.
    Analise a foto do item/equipamento encontrado e retorne APENAS um JSON válido no formato exato abaixo, sem marcações markdown extras:
    {
      "nome_item": "Nome identificado do item",
      "o_que_e": "Explicação clara do que é o equipamento e sua função original",
      "possivel_consertar": "Sim ou Não e uma breve justificativa de viabilidade",
      "veredito": "DEVE PEGAR" ou "NÃO DEVE PEGAR",
      "motivo_veredito": "Por que vale ou não a pena resgatar este item",
      "pecas_sucata": [
        {
          "nome": "Nome do componente extraível",
          "quantidade_estimada": 1,
          "utilidade": "Para que serve"
        }
      ]
    }"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Agora o Garimpo usa a lista dinâmica e atualizada!
    modelos_gratuitos = obter_modelos_visao_gratuitos()
    ultimo_erro = "Erro desconhecido."

    for modelo in modelos_gratuitos:
        payload = {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 1500
        }
        
        try:
            print(f"🔄 Garimpo tentando modelo: {modelo}")
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                conteudo = response.json()['choices'][0]['message']['content'].strip()
                if conteudo.startswith('```json'): conteudo = conteudo[7:]
                if conteudo.startswith('```'): conteudo = conteudo[3:]
                if conteudo.endswith('```'): conteudo = conteudo[:-3]
                
                try:
                    return json.loads(conteudo.strip())
                except json.JSONDecodeError:
                    continue
            else:
                detalhe_erro = response.json().get('error', {}).get('message', 'Erro desconhecido')
                ultimo_erro = f"O modelo {modelo} falhou. Motivo: {detalhe_erro}"
                continue
        except Exception as e:
            ultimo_erro = f"Timeout no modelo {modelo}: {str(e)}"
            continue

    return {
        "nome_item": "Item Desconhecido",
        "o_que_e": "Não foi possível analisar os detalhes.",
        "possivel_consertar": "Incerto",
        "veredito": "NÃO",
        "motivo_veredito": f"Todas as IAs dinâmicas falharam. Último erro: {ultimo_erro}",
        "pecas_sucata": []
    }