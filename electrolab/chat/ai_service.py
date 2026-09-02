import os

import requests
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)


def test_openrouter():

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY não foi encontrada."
        )

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },

        json={
            "model": "openrouter/free",

            "messages": [
                {
                    "role": "user",
                    "content": "Responda apenas: conexão funcionando."
                }
            ]
        },

        timeout=60,
    )

    print("STATUS:", response.status_code)
    print("RESPOSTA:", response.text)

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]