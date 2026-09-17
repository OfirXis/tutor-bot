"""Model downloads must target the server used for that model's app role."""
import io
import json

import pytest

from tools import install_translation_models as installer


@pytest.mark.parametrize(('selection', 'expected_url'), [
    ('intel', 'http://localhost:11435'),
    ('4b', 'http://localhost:11436'),
    ('all', 'http://localhost:11436'),
])
def test_installer_routes_models_and_keeps_all_translation_only(monkeypatch, capsys, selection, expected_url):
    monkeypatch.setenv('OLLAMA_BASE_URL', 'http://localhost:11435')
    monkeypatch.setenv('TRANSLATION_OLLAMA_BASE_URL', 'http://localhost:11436')
    monkeypatch.setattr('dotenv.load_dotenv', lambda *args, **kwargs: None)
    monkeypatch.setattr('sys.argv', ['install_translation_models.py', '--model', selection])
    pulled = []
    def request(value, **kwargs):
        if isinstance(value, str):
            assert value == expected_url + '/api/tags'
            return io.BytesIO(b'{"models": []}')
        assert value.full_url == expected_url + '/api/pull'
        pulled.append(json.loads(value.data)['model'])
        return io.BytesIO(b'{"status": "success"}\n')
    monkeypatch.setattr('urllib.request.urlopen', request)
    assert installer.main() == 0
    if selection == 'all':
        assert set(pulled) == set(installer.TRANSLATION_MODELS)
        assert installer.MODELS['intel'] not in pulled
    else:
        assert pulled == [installer.MODELS[selection]]
    if selection == 'intel':
        assert 'Provider → Ollama → Model' in capsys.readouterr().out
    else:
        assert 'Local translation model' in capsys.readouterr().out
