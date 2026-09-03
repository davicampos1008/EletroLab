import os
import json
import requests

def obter_modelos_visao_gratuitos():
    """Busca na API do OpenRouter todos os modelos 100% gratuitos do dia que suportam visão."""
    try:
        print("🔍 Buscando modelos gratuitos disponíveis hoje no OpenRouter...")
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
                    
                    # Filtra: deve aceitar imagem (na arquitetura ou pelo nome)
                    aceita_imagem = "image" in modality or "vision" in id_modelo or "vl" in id_modelo or "gemini" in id_modelo
                    
                    # Ignora: modelos de moderação (que respondem apenas 'safe' ou 'unsafe')
                    is_seguranca = "safety" in id_modelo or "moderation" in id_modelo
                    
                    if aceita_imagem and not is_seguranca:
                        modelos_validos.append(m["id"])
            
            # Mantém o openrouter/free na manga como último recurso caso o catálogo mude
            if "openrouter/free" not in modelos_validos:
                modelos_validos.append("openrouter/free")
                
            print(f"✅ Encontrados {len(modelos_validos)} modelos gratuitos de visão!")
            return modelos_validos
            
    except Exception as e:
        print(f"⚠️ Erro ao buscar modelos dinâmicos: {str(e)}")
        
    # Se a busca falhar por falta de internet temporária, usa fallback fixo seguro
    return ["google/gemnet-2.0-flash-lite-preview-02-05:free", "openrouter/free"]


def analisar_garimpo_sucata(base64_images_list):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

    # 1. CAÇADOR DINÂMICO DE MODELOS
    modelos_gratuitos = obter_modelos_visao_gratuitos()

    # 2. NOVO PROMPT FOCADO EM RECICLAGEM E EXTRAÇÃO DE PEÇAS
    prompt = """Você é um especialista em engenharia de campo, sucata eletrônica e garimpo de componentes para reaproveitamento.
    Analise as fotos do item/equipamento encontrado com foco estrito no **valor dos componentes internos para extração e estoque**. 
    O conserto do equipamento em si é apenas um bônus secundário; o principal é avaliar se vale a pena resgatar o item para colher peças valiosas (como microcontroladores, capacitores sólidos, MOSFETs, displays, motores, conectores, etc.).

    Retorne EXATAMENTE UM JSON VÁLIDO. Nenhuma palavra fora do JSON. Não use blocos markdown. 

    ESTRUTURA OBRIGATÓRIA DO JSON DE SAÍDA:
    {
      "nome_item": "Nome identificado do item ou sucata",
      "o_que_e": "Explicação breve do que é o equipamento",
      "possivel_consertar": "Viabilidade de reparo (bônus) e justificativa rápida",
      "veredito": "DEVE PEGAR" ou "NÃO DEVE PEGAR",
      "motivo_veredito": "Por que vale ou não a pena resgatar focado no lucro ou utilidade das peças de sucata",
      "pecas_sucata": [
        {
          "nome": "Nome do componente extraível",
          "quantidade_estimada": 1,
          "utilidade": "Para que serve na eletrônica/oficina"
        }
      ]
    }"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    conteudo_ia = [{"type": "text", "text": prompt}]
    for img_b64 in base64_images_list:
        conteudo_ia.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})

    # 3. LOOP DINÂMICO DE TENTATIVAS
    for modelo in modelos_gratuitos:
        try:
            print(f"🔄 Tentando analisar garimpo com: {modelo}...")
            
            payload = {
                "model": modelo,
                "messages": [
                    {
                        "role": "user",
                        "content": conteudo_ia
                    }
                ],
                "max_tokens": 2000
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                conteudo_bruto = data['choices'][0]['message']['content'].strip()
                
                if conteudo_bruto.startswith('```json'): conteudo_bruto = conteudo_bruto[7:]
                if conteudo_bruto.startswith('```'): conteudo_bruto = conteudo_bruto[3:]
                if conteudo_bruto.endswith('```'): conteudo_bruto = conteudo_bruto[:-3]
                conteudo_bruto = conteudo_bruto.strip()
                
                try:
                    return json.loads(conteudo_bruto)
                except json.JSONDecodeError:
                    print(f"⚠️ {modelo} gerou JSON inválido no Garimpo. Acionando próximo...")
                    continue 
            else:
                detalhes_erro = response.json().get("error", {}).get("message", "Sem detalhes")
                print(f"⚠️ Erro {response.status_code} no {modelo}: {detalhes_erro}")
                continue
                
        except Exception as e:
            print(f"⚠️ Timeout ou falha no {modelo}: {str(e)}")
            continue

    print("❌ Falha crítica: Todos os modelos disponíveis falharam no Garimpo.")
    return {
        "nome_item": "Item Desconhecido",
        "o_que_e": "Não foi possível analisar os detalhes.",
        "possivel_consertar": "Incerto",
        "veredito": "NÃO",
        "motivo_veredito": "Nossas IAs estão instáveis no momento.",
        "pecas_sucata": []
    }