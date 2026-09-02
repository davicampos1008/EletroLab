import os
import requests
import json

def analisar_pecas_para_estoque(base64_image):
    """
    Analisa uma placa ou equipamento e retorna uma lista limpa de peças 
    que podem ser extraídas para o estoque.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    prompt = """Você é um especialista em engenharia reversa e eletrônica. 
    Analise a imagem da placa ou equipamento fornecida e liste os principais componentes reaproveitáveis que podem ser salvos em um estoque de peças.
    
    Retorne APENAS um JSON válido no seguinte formato exato, sem marcações markdown extras:
    {
      "nome_equipamento": "Nome do equipamento ou placa identificada",
      "pecas": [
        {
          "nome": "Nome do componente (Ex: Microcontrolador ATmega328P, Capacitor Eletrolítico 25V 1000uF)",
          "quantidade_estimada": 1,
          "utilidade": "Breve descrição de para que serve"
        }
      ]
    }"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "google/gemini-2.0-flash-lite-preview-02-05:free",
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
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            conteudo = response.json()['choices'][0]['message']['content'].strip()
            if conteudo.startswith('```json'): conteudo = conteudo[7:]
            if conteudo.startswith('```'): conteudo = conteudo[3:]
            if conteudo.endswith('```'): conteudo = conteudo[:-3]
            return json.loads(conteudo.strip())
    except Exception as e:
        print(f"Erro ao extrair peças: {e}")
    
    return {"nome_equipamento": "Placa Genérica", "pecas": []}