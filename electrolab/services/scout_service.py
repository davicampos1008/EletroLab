import os
import requests
import json

def obter_modelos_visao_gratuitos():
    """Busca na API do OpenRouter todos os modelos 100% gratuitos do dia que suportam visão, descartando áudio e texto puro."""
    try:
        print("🔍 Buscando modelos gratuitos disponíveis hoje no OpenRouter para o Garimpo...")
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        
        if response.status_code == 200:
            modelos = response.json().get("data", [])
            modelos_validos = []
            
            for m in modelos:
                pricing = m.get("pricing", {})
                # Garante que o custo de envio e resposta seja absolutamente ZERO
                is_free = str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0"
                
                if is_free:
                    id_modelo = m.get("id", "").lower()
                    arch = m.get("architecture", {})
                    modality = arch.get("modality", "").lower()
                    
                    # Filtros estritos para garantir visão e bloquear áudio/música
                    is_audio_ou_musica = "lyria" in id_modelo or "audio" in id_modelo or "voice" in id_modelo or "tts" in id_modelo
                    is_seguranca = "safety" in id_modelo or "moderation" in id_modelo
                    
                    aceita_imagem = "image" in modality or "vision" in id_modelo or "vl" in id_modelo or "gemini" in id_modelo or "flash" in id_modelo or "pro" in id_modelo
                    
                    if aceita_imagem and not is_audio_ou_musica and not is_seguranca:
                        modelos_validos.append(m["id"])
            
            # Mantém o fallback seguro na manga caso o catálogo mude
            if "google/gemini-2.0-flash-lite-preview-02-05:free" not in modelos_validos:
                modelos_validos.insert(0, "google/gemini-2.0-flash-lite-preview-02-05:free")
            if "openrouter/free" not in modelos_validos:
                modelos_validos.append("openrouter/free")
                
            print(f"✅ Encontrados {len(modelos_validos)} modelos gratuitos de visão seguros para o Garimpo!")
            return modelos_validos
            
    except Exception as e:
        print(f"⚠️ Erro ao buscar modelos dinâmicos no Garimpo: {str(e)}")
        
    # Fallback seguro padrão caso a API caia temporariamente
    return [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "google/gemini-1.5-flash:free",
        "openrouter/free"
    ]

def analisar_garimpo_sucata(base64_images_list):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

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

    modelos_gratuitos = obter_modelos_visao_gratuitos()
    ultimo_erro = "Erro desconhecido."
    
    # Prepara o conteúdo unificando o prompt de texto com a lista de imagens enviadas
    conteudo_ia = [{"type": "text", "text": prompt}]
    for img_b64 in base64_images_list:
        conteudo_ia.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})

    for modelo in modelos_gratuitos:
        payload = {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": conteudo_ia
                }
            ],
            "max_tokens": 1500
        }
        
        try:
            print(f"🔄 Garimpo testando modelo dinâmico: {modelo}...")
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                conteudo = data['choices'][0]['message']['content'].strip()
                
                # Limpeza rigorosa de blocos markdown
                if conteudo.startswith('```json'): conteudo = conteudo[7:]
                if conteudo.startswith('```'): conteudo = conteudo[3:]
                if conteudo.endswith('```'): conteudo = conteudo[:-3]
                
                try:
                    return json.loads(conteudo.strip())
                except json.JSONDecodeError:
                    print(f"⚠️ {modelo} retornou JSON inválido no Garimpo. Tentando próximo...")
                    continue
            else:
                try:
                    detalhe_erro = response.json().get('error', {}).get('message', 'Erro desconhecido')
                except:
                    detalhe_erro = response.text
                ultimo_erro = f"O modelo {modelo} falhou. Motivo: {detalhe_erro}"
                print(f"⚠️ {ultimo_erro}")
                continue
                
        except Exception as e:
            ultimo_erro = f"Timeout ou falha no modelo {modelo}: {str(e)}"
            print(f"⚠️ {ultimo_erro}")
            continue

    print("❌ Falha crítica no Garimpo: Todos os modelos disponíveis falharam.")
    return {
        "nome_item": "Item Desconhecido",
        "o_que_e": "Não foi possível analisar os detalhes.",
        "possivel_consertar": "Incerto",
        "veredito": "NÃO",
        "motivo_veredito": f"Todas as IAs filtradas falharam. Último erro: {ultimo_erro}",
        "pecas_sucata": []
    }