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

def analisar_garimpo_sucata(base64_images_list): # Agora recebe a lista
    api_key = os.environ.get("OPENROUTER_API_KEY")
    prompt = """Você é um especialista em engenharia de campo... (mantenha seu prompt igual)"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    modelos_gratuitos = obter_modelos_visao_gratuitos()
    ultimo_erro = "Erro desconhecido."
    
    # Prepara o conteúdo misturando o texto e TODAS as imagens
    conteudo_ia = [{"type": "text", "text": prompt}]
    for img_b64 in base64_images_list:
        conteudo_ia.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})

    for modelo in modelos_gratuitos:
        payload = {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": conteudo_ia # Envia a lista montada aqui!
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