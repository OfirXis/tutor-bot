"""Downloadable Ollama presets for Hebrew model experiments."""
HEBREW_MODELS = {
    "translategemma:4b":
        ("TranslateGemma — 4B parameters — Q4", "Dedicated translation model; approximately 3.3 GB download. Hebrew/English translation candidate."),
    'hf.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF:Q4_K_M':
        ('DictaLM 3.0 Instruct — 1.7B parameters — Q4', 'Small bilingual translation candidate; community quantization.'),
    'hf.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF:Q4_K_M':
        ('DictaLM 3.0 Nemotron Instruct — 12B parameters — Q4', 'Larger bilingual candidate for 16 GB VRAM; allow room for context and tutor.'),
    'hf.co/mradermacher/hebrew-math-tutor-v1-GGUF:Q4_K_M':
        ('Intel Hebrew Math Tutor v1 — 4B parameters — Q4', 'Math answering experiment; translation fidelity is untested. Community quantization.'),
}


TRANSLATION_MODELS = {model: info for model, info in HEBREW_MODELS.items()
                      if 'DictaLM' in info[0] or model.startswith('translategemma:')}
TUTOR_MODELS = {model: info for model, info in HEBREW_MODELS.items()
                if model not in TRANSLATION_MODELS}


def model_options(installed: list[str], role: str = 'tutor') -> list[str]:
    presets = TRANSLATION_MODELS if role == 'translation' else TUTOR_MODELS
    excluded = TUTOR_MODELS if role == 'translation' else TRANSLATION_MODELS
    return list(dict.fromkeys([*(model for model in installed if model not in excluded),
                               *presets]))


def model_label(model: str) -> str:
    return HEBREW_MODELS.get(model, (model, ''))[0]


def translation_fallback_model(selected: str, installed: list[str]) -> str | None:
    """Use only the installed larger DictaLM as fallback for the small preset."""
    if selected not in TRANSLATION_MODELS or '1.7B' not in selected:
        return None
    return next((model for model in TRANSLATION_MODELS
                 if '12B' in model and model in installed), None)
