# Hebrew support and local translation models

Detailed guide to the Hebrew pipeline and local translator models. See the [README](../README.md) for setup.

## Hebrew support

Select **עברית** from the language control in the sidebar for Hebrew labels,
right-to-left input, and localized course titles. Hebrew questions are detected
automatically even when the interface remains in English.

The retrieval index stays in English: Hebrew questions are translated before
retrieval, and answers are translated back while code and math are preserved
verbatim. The student sees only the Hebrew response; English stays inside retrieval
and model history. The tutor and translator can use completely different models.
Select the translation provider and local model name under **Hebrew / עברית** in
the sidebar, or configure `.env`:

```dotenv
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=dictalm-translator
TRANSLATION_OLLAMA_BASE_URL=http://localhost:11434
TRANSLATION_NUM_CTX=4096
```

The local model must already be installed/imported in Ollama under that name.
`dictalm-translator` is an example local alias, not a built-in downloadable tag.
Explicit local selection does not silently switch to OpenAI or the tutoring model
on failure. `auto` preserves the previous behavior: OpenAI when a key exists,
otherwise the selected tutor. `tutor` explicitly shares the tutor; `openai` uses
`TRANSLATION_MODEL` and requires a key. Set `UI_LANGUAGE=he` for Hebrew UI labels.

Candidate to test on a 4 GB GPU: [DictaLM 3.0 1.7B Instruct](https://huggingface.co/dicta-il/DictaLM-3.0-1.7B-Instruct),
preferably quantized. Its bilingual training makes it a plausible translator;
translation quality for algorithms must still be checked. Larger DictaLM variants
need substantially more memory or CPU offloading. [Intel Hebrew Math Tutor v1](https://huggingface.co/Intel/hebrew-math-tutor-v1)
is a 4B thinking model specialized for Hebrew math answers, rather than a dedicated
translation model. Use it as a tutoring experiment before choosing it for literal
translation. No new Hebrew model has been downloaded or quality-benchmarked here.
Two local models may compete for GPU memory and need to be loaded sequentially.

### Installing local Hebrew translation models

Model weights are downloaded by Ollama, not by `pip` or `requirements.txt`.
Install or update [Ollama](https://ollama.com/download), start the Ollama desktop
app, and open a new PowerShell terminal. Verify it is running:

```powershell
ollama --version
ollama list
```

If the terminal cannot find `ollama`, reopen it after installation. If the server
is unavailable, start the Ollama app; on systems without its background service,
run `ollama serve` in a separate terminal. Run downloads on the machine hosting
Ollama (the default app connection is `http://localhost:11434`).

| Translation model | Parameters | Quantization | Weight download, approximately |
| --- | --- | --- | --- |
| TranslateGemma | 4 billion | Q4_K_M | 3.3 GB |
| DictaLM 3.0 Instruct | 1.7 billion | Q4_K_M | 1.11 GB |
| DictaLM 3.0 Nemotron Instruct | 12 billion | Q4_K_M | 7.49 GB |

Sizes describe weight files, not total GPU memory requirements. The 1.7B preset
uses a community conversion; the 12B preset uses DICTA's GGUF release. See the
[1.7B repository](https://huggingface.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF)
and [12B repository](https://huggingface.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF).

Download the lighter dedicated translator first:

```powershell
ollama pull translategemma:4b
```

The older DictaLM 1.7B experiment can be installed with
`ollama pull hf.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF:Q4_K_M`.

Download the larger translator to compare them:

```powershell
ollama pull hf.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF:Q4_K_M
ollama list
```

Keep the exact model names, including `hf.co/` and `:Q4_K_M`, so they match the
app presets. The same download commands work on Linux/macOS.

From the project directory, launch the app:

```powershell
.\run.ps1
```

Open **Hebrew / עברית** in the sidebar, choose **Ollama** as the translation
provider, and select **TranslateGemma — 4B parameters — Q4**,
**DictaLM 3.0 Instruct — 1.7B parameters — Q4**, or
**DictaLM 3.0 Nemotron Instruct — 12B parameters — Q4** under **Local translation
model**. Keep your answering model selected separately under **Model**.

To make a translator the startup default, add these settings to `.env` without
replacing your existing tutor or API settings:

```dotenv
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=hf.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF:Q4_K_M
TRANSLATION_OLLAMA_BASE_URL=http://localhost:11434
TRANSLATION_NUM_CTX=4096
```

For the 12B default, replace just the model setting:

```dotenv
TRANSLATION_OLLAMA_MODEL=hf.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF:Q4_K_M
```

Restart the app after changing `.env`. Test a Hebrew question about an allowed
topic, for example `מה זה דייקסטרה?` at week 9. Compare both translators for
meaning, algorithm names, exclusions such as “without Dijkstra,” formulas, and
source references. An English question should still use the tutor directly.
See the local translation smoke checks below; these are small samples, not a complete quality benchmark.

With 16 GB VRAM, start with TranslateGemma 4B and a small answering model.
Context and both models need additional memory; fitting both simultaneously is
not guaranteed. `ollama ps` shows currently loaded models. You can stop an unused
model with `ollama stop MODEL_NAME`, or reduce `TRANSLATION_NUM_CTX` if necessary.

If a download fails, update Ollama, verify the exact model name, and check access
to Hugging Face. If the app still labels a freshly downloaded model as missing,
wait 30 seconds and interact again (installed-model discovery is cached), or
restart the app. A “model not found” error means the selected name is not installed
on the Ollama server the app connects to. Do not use the example alias
`dictalm-translator` unless you have explicitly created that alias.

### Install Intel Hebrew Math Tutor and TranslateGemma 4B, step by step

The models have different roles:

| Model | Parameters | Select it under |
| --- | --- | --- |
| [Intel Hebrew Math Tutor v1](https://huggingface.co/Intel/hebrew-math-tutor-v1) | About 4B | **Provider → Ollama → Model** (answering) |
| [TranslateGemma](https://ollama.com/library/translategemma:4b) | 4B model family | **Hebrew / עברית → Ollama → Local translation model** |

The Intel Ollama preset uses a [community GGUF conversion](https://huggingface.co/mradermacher/hebrew-math-tutor-v1-GGUF)
of Intel's model. TranslateGemma downloads about 3.3 GB. The Intel model is an
optional answering experiment; selecting it still uses the app's normal
Hebrew → English → tutor → Hebrew pipeline.

1. Start the Ollama application/server. Open a terminal **in this project's
   directory**, where `run.py` and `tools/` are located. Use the terminal on the
   machine whose Ollama server the app connects to.
2. If `ollama` is not recognized, use the Python helper below. Ollama must be
   running, but its command does not need to be on PATH. The two install commands
   are independent; run the one for each model you want.

**Linux / WSL — including a terminal whose project path starts with `/home/Asaf`:**

```bash
.venv/bin/python tools/install_translation_models.py --model intel
.venv/bin/python tools/install_translation_models.py --model 4b
.venv/bin/python tools/install_translation_models.py --list
```

**Windows PowerShell:**

```powershell
.\.venv\Scripts\python.exe tools/install_translation_models.py --model intel
.\.venv\Scripts\python.exe tools/install_translation_models.py --model 4b
.\.venv\Scripts\python.exe tools/install_translation_models.py --list
```

If the virtual-environment Python does not exist yet, run `python3 run.py
--setup-only` on Linux/WSL or `py -3 run.py --setup-only` in Windows PowerShell,
then retry. If using another Python environment with the project dependencies,
you can use `python tools/install_translation_models.py ...` instead.

If `ollama` works in your terminal, these are the equivalent downloads on either
platform:

```bash
ollama pull hf.co/mradermacher/hebrew-math-tutor-v1-GGUF:Q4_K_M
ollama pull translategemma:4b
ollama list
```

3. Wait for `success` / `Installed` before selecting the model. Running a pull
   again reuses already-downloaded layers. The helper's `--model all` downloads
   only translation presets; Intel requires the explicit `--model intel` option.
4. Restart the app: `./run.sh` on Linux/WSL or `.\run.ps1` on Windows.
5. To test Intel, set **Provider = Ollama** and **Model = Intel Hebrew Math Tutor
   v1 — 4B parameters — Q4**. Under **Hebrew / עברית**, set **Translation provider
   = Ollama** and **Local translation model = TranslateGemma — 4B parameters — Q4**.
6. Choose week 9 and try `What is dynamic programming?`, then `מה זה תכנות דינמי?`.
   This checks the answering model first, then the full Hebrew pipeline. Intel
   is a reasoning model and may take longer than a lightweight chat model.

For persistent startup selections, edit just these keys in `.env`, keeping your
other settings:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_LLM_MODEL=hf.co/mradermacher/hebrew-math-tutor-v1-GGUF:Q4_K_M
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=translategemma:4b
```

If a model is missing from the dropdown, wait 30 seconds for the installed-model
cache or restart the app. The model must be installed on the same Ollama server
used by the corresponding selector. The helper uses `OLLAMA_BASE_URL` for Intel
and `TRANSLATION_OLLAMA_BASE_URL` (falling back to `OLLAMA_BASE_URL`) for translation
models. Override either with `--url http://HOST:11434`. With separate servers,
use `--model intel --list` to check the answering server and `--list` to check the
translation server. A connection error means the server must be started or its
URL corrected; installing a Python package will not download these model weights.

### Hebrew testing presets

The local translation selector includes DictaLM 3.0 1.7B Instruct and DictaLM 3.0
Nemotron 12B Instruct. The Ollama tutor selector includes Intel Hebrew Math Tutor v1.
All three are Q4_K_M GGUF presets, listed under their intended roles. Each uninstalled selection shows its exact `ollama pull` command.
Run that command on the machine hosting Ollama, then select the model to test.
The 1.7B and Intel presets use community quantizations; the 12B uses DICTA's release.
These are selectable candidates, not downloaded or quality-validated models.
Translation still uses the separate Hebrew → English → tutor → Hebrew pipeline.


### If `ollama` is not found

The app uses Ollama's HTTP API; its command-line executable is not required if
an Ollama server is already running. You can download the translation models
using the project's Python helper instead:

```powershell
python tools/install_translation_models.py --list
python tools/install_translation_models.py --model 1.7b
python tools/install_translation_models.py --model 12b
```

Use `py -3` instead of `python` if that is your Windows Python command, or
`python3` on Linux/macOS. `--model all` installs both. The helper reads `.env`
server settings; `--url http://YOUR_SERVER:11434` overrides them. Downloads are
stored on that Ollama server, not in this project's Python environment.

If no server is reachable, install/start Ollama first. On Windows, install it
from https://ollama.com/download/windows, then restart VS Code and its terminal.
The default executable is `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`; test it
in PowerShell with:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
```

If this works but `ollama --version` does not, the terminal's PATH is stale or
missing that install directory. Restart the terminal first. On Linux, follow
https://docs.ollama.com/linux for installation on the machine hosting Ollama.

Local translators translate complete sentences in bounded blocks, rather than
splitting sentences around formulas. Code and formulas use checked placeholders;
citation IDs are checked and their original text restored. Long homework answers
are split before they exceed the output budget. One repair attempt is allowed
per translation.
Simple Hebrew requests for a known course topic (such as `ספר לי על הפרד ומשול`)
use the curriculum's exact English topic name, preventing the translator from
changing the question to a different algorithm.

Hebrew chat messages use right-to-left direction and right alignment regardless
of the sidebar language. Code blocks and formulas retain left-to-right direction.

### Local translation speed and quality

Translation progress shows elapsed seconds and generated character counts.
Local translation disables model reasoning, uses a 4096-token context, limits
output to 768 tokens per block, and keeps the translator loaded for 10 minutes. A 45-second
network timeout and elapsed-time checks stop stalled generation. An answer that
hits its output limit is rejected rather than displayed as a partial translation.
Configure these values in `.env`, then restart the app:

```ini
TRANSLATION_NUM_CTX=4096
TRANSLATION_MAX_TOKENS=768
TRANSLATION_TIMEOUT_SECONDS=45
TRANSLATION_KEEP_ALIVE=10m
```

For the 12B model on a 16 GB GPU, run `ollama ps` while translating and check the
PROCESSOR column. CPU or mixed CPU/GPU execution can explain long delays. Close
other GPU applications and stop unused models with `ollama stop MODEL_NAME`.
Reducing `TRANSLATION_NUM_CTX` to 2048 can reduce memory pressure for short
answers. Increasing context or output limits consumes more memory or time.
The first request may take longer while weights load; progress begins when
Ollama sends output. Check the error details panel if translation fails.

The 1.7B model remains less reliable: structured output and course-term checks
reduce topic drift and reject visible corruption, but cannot guarantee faithful
translation. It translated a short divide-and-conquer sample correctly in local
testing; a sentence split around a formula still failed language validation.
Use the 12B translator for better fidelity. Rejected translations show an error
and its details instead of garbled text; the English answer is not substituted
for the requested Hebrew response.


### Relevant-week refusals and Hebrew translation recovery

Course shorthand such as `DP`, `dc`, and `D&C` is expanded in recognizable
algorithm questions before scope checks, homework clarification, and retrieval.
This does not depend on the answering model returning valid normalization JSON.
Code, formulas, and non-course meanings such as Washington DC remain untouched.
Example requests also retrieve a worked example from a relevant course source
when available. Week restrictions and evidence checks still apply.

Hebrew translations no longer require English course titles to remain English
when the curriculum lacks Hebrew aliases. Invalid nested JSON and changed source
citations are rejected. If both DictaLM presets are installed, selecting the 1.7B
translator shows **Retry failed translations with the installed 12B model**
(enabled by default). You can turn this off to test the smaller model alone.
The fallback uses the same Ollama translation server and downloads nothing.
Each model has its own translation timeout, so a fallback may add another wait.

These checks do not establish semantic translation accuracy. The small model can
still mistranslate technical prose, and even the larger model needs review for
mathematical homework. TranslateGemma 4B is the lighter dedicated option; compare
it with the 12B model for your questions and treat DictaLM 1.7B as experimental. Restart the app after updating to load these changes.


### Lighter dedicated translator: TranslateGemma 4B

[TranslateGemma 4B](https://ollama.com/library/translategemma:4b) is a dedicated
translation model with an approximately 3.3 GB Ollama download. Install it with:

```bash
python tools/install_translation_models.py --model 4b
```

Or, if the Ollama command is available:

```bash
ollama pull translategemma:4b
```

Restart the app, open **Hebrew / עברית**, select **Ollama** as the translation
provider, and choose **TranslateGemma — 4B parameters — Q4**. It is listed under
translation models, not the answering-model presets. To make it the startup
selection, set these values in `.env`:

```ini
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=translategemma:4b
```

The app uses [TranslateGemma's native single-user translation prompt](https://ollama.com/library/translategemma),
with explicit English/Hebrew language codes and plain-text output. This model
must not use the JSON instruction format used for the general chat translators.
The same timeout, block-size, formula, and citation checks still apply. The 12B
fallback checkbox remains specific to the small DictaLM preset; selecting
TranslateGemma tests TranslateGemma itself.


Local smoke check: TranslateGemma completed two Hebrew-to-English questions and
four English-to-Hebrew answers (flow, DP, a divide-and-conquer example, and
Homework 5 problem 4 guidance) without a fallback. Warm answer translation took
about 0.8–2.3 seconds, versus 1.7–4.6 seconds for DictaLM 12B on the same inputs.
Initial model loading took longer. These are local sample measurements, not a
speed or accuracy guarantee; Hebrew phrasing can still be awkward. The app
normalizes a few known literal translations to the course terminology and
restores translated citation labels when their IDs match. If citations drift, it
keeps the translated prose and appends the original references at the end of
the affected block instead of rejecting the translation.
Results: `eval/translategemma_4b_smoke.json`.


### Translation failed even though the model is installed

A translation error is not necessarily an installation error. The chat now
separates unavailable models, connection failures, timeouts, and output-validation
failures. The **Translation error / שגיאת תרגום** panel stays attached to the
message after a page rerun, so its underlying error remains available.

Hebrew wording is no longer rejected simply because it is absent from the short
curriculum alias list. English retrieval queries still retain explicit topic
checks, and translated answers still undergo language, citation, and corruption
checks. Standalone code and formulas are copied without a translation request.
If TranslateGemma drops inline formula placeholders, one bounded retry presents
the original notation. Its protected spans must match before the original math
is restored; altered equations are rejected. This does not automatically switch
to a larger model.
