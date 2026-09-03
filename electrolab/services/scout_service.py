import os
import requests
import json

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

    modelos_gratuitos = [
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "google/gemini-2.0-pro-exp-02-05:free",
        "google/gemini-exp-1206:free"
    ]

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
            ]
        }
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                conteudo = response.json()['choices'][0]['message']['content'].strip()
                if conteudo.startswith('```json'): conteudo = conteudo[7:]
                if conteudo.startswith('```'): conteudo = conteudo[3:]
                if conteudo.endswith('```'): conteudo = conteudo[:-3]
                return json.loads(conteudo.strip())
            else:
                try:
                    detalhe_erro = response.json().get('error', {}).get('message', response.text)
                except:
                    detalhe_erro = response.text
                ultimo_erro = f"O modelo {modelo} falhou. Motivo: {detalhe_erro}"
                print(ultimo_erro)
                continue
        except Exception as e:
            ultimo_erro = f"Timeout no modelo {modelo}: {str(e)}"
            print(ultimo_erro)
            continue

    return {
        "nome_item": "Item Desconhecido",
        "o_que_e": "Não foi possível analisar os detalhes.",
        "possivel_consertar": "Incerto",
        "veredito": "NÃO",
        "motivo_veredito": f"Todas as IAs falharam. {ultimo_erro}",
        "pecas_sucata": []
    }