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
    return ["google/gemini-2.0-flash-lite-preview-02-05:free", "openrouter/free"]


def analisar_imagem_qwen(base64_image):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

    # 1. CHAMA O CAÇADOR DINÂMICO
    modelos_gratuitos = obter_modelos_visao_gratuitos()

    # 2. PROMPT PROFISSIONAL
    prompt_sistema = """Você é um assistente de IA altamente avançado com duas funções principais:
    1. Um Engenheiro Eletrônico/Mecânico Especialista.
    2. Uma ferramenta de reconhecimento visual universal (estilo Google Lens).

    Analise a imagem com extrema precisão e retorne EXATAMENTE UM JSON VÁLIDO. Nenhuma palavra fora do JSON. Não use blocos markdown. 

    Siga esta lógica rigorosamente:
    - Verifique se a imagem contém eletrônicos, placas, robótica, programação, ferramentas ou maquinário. Se sim, defina "is_tecnico" como true e preencha "dados_tecnicos".
    - Se for qualquer outra coisa, defina "is_tecnico" como false e preencha "dados_gerais" com o máximo de conhecimento.
    - NUNCA invente informações. Seja preciso e direto.

    ESTRUTURA OBRIGATÓRIA DO JSON DE SAÍDA:
    {
        "is_tecnico": true ou false,
        "resumo_imagem": "Resumo do que é a imagem",
        "dados_tecnicos": {
            "equipamento_ou_placa": "Nome completo e marca",
            "funcao_principal": "Para que serve?",
            "diagnostico_reparo": "Dicas de conserto/teste",
            "guia_desmontagem": "Instruções de desmontagem seguras",
            "pecas_para_estoque": [
                {"nome": "Componente", "utilidade": "Para que serve", "estado_visivel": "bom/queimado"}
            ]
        },
        "dados_gerais": {
            "nome_objeto": "O que é?",
            "descricao_detalhada": "Descrição completa",
            "curiosidades_ou_instrucoes": "Como usar/cuidar"
        }
    }"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 3. LOOP DINÂMICO ANTI-FALHAS
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
                "max_tokens": 2000 # Previne recusas da API
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                conteudo_bruto = data['choices'][0]['message']['content'].strip()
                
                # Limpeza de formatação
                if conteudo_bruto.startswith('```json'): conteudo_bruto = conteudo_bruto[7:]
                if conteudo_bruto.startswith('```'): conteudo_bruto = conteudo_bruto[3:]
                if conteudo_bruto.endswith('```'): conteudo_bruto = conteudo_bruto[:-3]
                conteudo_bruto = conteudo_bruto.strip()
                
                try:
                    return json.loads(conteudo_bruto)
                except json.JSONDecodeError:
                    print(f"⚠️ {modelo} gerou JSON inválido. Acionando fallback...")
                    continue 
            else:
                detalhes_erro = response.json().get("error", {}).get("message", "Sem detalhes")
                print(f"⚠️ Erro {response.status_code} no {modelo}: {detalhes_erro}")
                continue
                
        except Exception as e:
            print(f"⚠️ Timeout ou falha no {modelo}: {str(e)}")
            continue

    print("❌ Falha crítica: Todos os modelos disponíveis falharam.")
    return {
        "is_tecnico": False,
        "resumo_imagem": "Falha de comunicação com as IAs.",
        "dados_tecnicos": None,
        "dados_gerais": {
            "nome_objeto": "Erro de Servidor",
            "descricao_detalhada": "Nossas IAs estão instáveis no momento.",
            "curiosidades_ou_instrucoes": "Tente novamente mais tarde."
        }
    }