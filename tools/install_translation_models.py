"""Download app model presets through Ollama's API; no ollama CLI needed.

Run from the project: python tools/install_translation_models.py --model 1.7b
Use --model 4b for TranslateGemma or --model intel for Intel Hebrew Math Tutor.
Use --model all for all translation presets (excludes the Intel answering model).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_models import TRANSLATION_MODELS, TUTOR_MODELS

MODELS = {
    '4b': 'translategemma:4b',
    'intel': next(model for model in TUTOR_MODELS if 'hebrew-math-tutor-v1' in model),
    '1.7b': next(model for model in TRANSLATION_MODELS if '1.7B' in model),
    '12b': next(model for model in TRANSLATION_MODELS if '12B' in model),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=[*MODELS, 'all'], default='4b')
    parser.add_argument('--list', action='store_true', help='Only list installed server models')
    parser.add_argument('--url', help='Ollama server URL, overriding environment settings')
    args = parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
    except ImportError:
        pass
    default_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    if args.model != 'intel':
        default_url = os.getenv('TRANSLATION_OLLAMA_BASE_URL') or default_url
    url = (args.url or default_url).rstrip('/')
    try:
        with urllib.request.urlopen(url + '/api/tags', timeout=10) as response:
            installed = json.load(response)
        print(f'Ollama server: {url}')
        for model in installed.get('models', []):
            print(model['name'])
        if args.list:
            return 0
        selected = list(TRANSLATION_MODELS) if args.model == 'all' else [MODELS[args.model]]
        for model in selected:
            print(f'Downloading {model}', flush=True)
            request = urllib.request.Request(
                url + '/api/pull',
                data=json.dumps({'model': model, 'stream': True}).encode(),
                headers={'Content-Type': 'application/json'}, method='POST')
            last = None
            with urllib.request.urlopen(request, timeout=600) as response:
                for line in response:
                    event = json.loads(line)
                    if event.get('error'):
                        raise RuntimeError(event['error'])
                    total, completed = event.get('total', 0), event.get('completed', 0)
                    progress = int(completed * 100 / total) if total else None
                    state = (event.get('status', ''), progress)
                    if state != last:
                        print(state[0] + (f' {progress}%' if progress is not None else ''), flush=True)
                        last = state
            if not last or last[0] != 'success':
                raise RuntimeError('Download ended without confirmation of success')
        if args.model == 'intel':
            print('Installed. Select Intel Hebrew Math Tutor under Provider → Ollama → Model in the app.')
        else:
            print('Installed. Select the model under Hebrew / עברית → Ollama → Local translation model in the app.')
        return 0
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as error:
        print(f'Ollama request failed: {error}', file=sys.stderr)
        print('Start the Ollama application/server, or pass --url for the server you use.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
