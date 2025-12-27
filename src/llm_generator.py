import os
import requests
import json

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


def generate_with_openai(brief, attachments):
    """Call OpenAI Chat Completions to generate a small web app scaffold.

    Returns a dict of filename -> content. Keep this simple and expect small outputs.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY not set')

    system = (
        "You are a code generator. Given a brief and attachments, produce a JSON object mapping filenames to file contents. "
        "Only return the JSON object and nothing else. Files should be small and safe (no secrets)."
    )

    user = json.dumps({"brief": brief, "attachments": attachments})

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ],
        'temperature': 0.2,
        'max_tokens': 1500
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Get the assistant text
    text = data['choices'][0]['message']['content']

    # Expect the model to return pure JSON mapping filenames to contents
    try:
        files = json.loads(text)
    except Exception:
        # If the model returns code fences or surrounding text, attempt to extract JSON
        import re
        m = re.search(r"(\{[\s\S]*\})", text)
        if not m:
            raise
        files = json.loads(m.group(1))

    return files
