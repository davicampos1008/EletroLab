import os
import json
import requests

def obter_modelos_visao_gratuitos():
    """Busca na API do OpenRouter e pega apenas os 3 melhores para não travar o servidor."""
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", timeout=8)
        
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
                
            # 🔒 TRAVA DE SEGURANÇA: Retorna no máximo 3 modelos para o Gunicorn não dar timeout!
            return modelos_validos[:3]
            
    except Exception as e:
        print(f"⚠️ Erro ao buscar modelos: {str(e)}")
        
    return ["google/gemini-2.0-flash-lite-preview-02-05:free", "openrouter/free"]


def analisar_imagem_qwen(base64_image):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("A chave OPENROUTER_API_KEY não foi encontrada.")

    modelos_gratuitos = obter_modelos_visao_gratuitos()

    prompt_sistema = """Você é um Engenheiro Eletrônico. 
    Analise a imagem e retorne EXATAMENTE UM JSON VÁLIDO.
    {
        "is_tecnico": true ou false,
        "resumo_imagem": "Resumo curto",
        "dados_tecnicos": {
            "equipamento_ou_placa": "Nome completo",
            "funcao_principal": "Para que serve?",
            "diagnostico_reparo": "Dicas de conserto",
            "guia_desmontagem": "Instruções",
            "pecas_para_estoque": [{"nome": "Componente", "utilidade": "Uso", "estado_visivel": "bom/ruim"}]
        },
        "dados_gerais": {
            "nome_objeto": "O que é?",
            "descricao_detalhada": "Descrição",
            "curiosidades_ou_instrucoes": "Como usar"
        }
    }"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for modelo in modelos_gratuitos:
        try:
            print(f"🔄 Tentando analisar com: {modelo}...")
            
            payload = {
                "model": modelo,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_sistema},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                "max_tokens": 1500
            }
            
            # 🔒 DIMINUÍDO DE 25s PARA 12s: Se demorar mais que 12s, aborta e tenta o próximo!
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=12)
            
            if response.status_code == 200:
                data = response.json()
                conteudo_bruto = data.get('choices', [{}])[0].get('message', {}).get('content')
                
                if not conteudo_bruto:
                    continue
                    
                conteudo_bruto = conteudo_bruto.strip()
                if conteudo_bruto.startswith('```json'): conteudo_bruto = conteudo_bruto[7:]
                if conteudo_bruto.startswith('```'): conteudo_bruto = conteudo_bruto[3:]
                if conteudo_bruto.endswith('```'): conteudo_bruto = conteudo_bruto[:-3]
                
                try:
                    return json.loads(conteudo_bruto.strip())
                except json.JSONDecodeError:
                    continue 
            else:
                continue
                
        except Exception as e:
            continue

    return {
        "is_tecnico": False,
        "resumo_imagem": "Falha de comunicação com as IAs (Tempo Esgotado).",
        "dados_tecnicos": None,
        "dados_gerais": {
            "nome_objeto": "Erro de Servidor",
            "descricao_detalhada": "As IAs demoraram muito para responder.",
            "curiosidades_ou_instrucoes": "Tente imagens com menos detalhes ou aguarde."
        }
    }