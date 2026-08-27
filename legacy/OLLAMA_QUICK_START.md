# ⚡ 3-Minute Ollama Quick Install (for tutor-bot-ollama)

## 🎯 Your Hardware Summary
- **CPU:** AMD Ryzen 9 8940HX (16 cores, 32 threads) ✅ Excellent
- **RAM:** 32 GB ✅ Perfect
- **GPU:** NVIDIA RTX 5070 Laptop GPU (4 GB VRAM) ✅ Great for CUDA
- **Disk:** 1500+ GB free ✅ Plenty of space

---

## 📥 Install Ollama (2 minutes)

### Step 1: Download
https://ollama.ai/download/windows → OllamaSetup.exe

### Step 2: Run installer
- Click "OllamaSetup.exe" and follow the wizard
- Default location is fine
- It will start automatically

### Step 3: Verify
Open PowerShell and run:
```powershell
ollama --version
# Output should be: ollama version 0.x.x
```

---

## 🚀 Download a Model (1 minute)

Open PowerShell and pick ONE:

### ⭐ **Recommended: Mistral 7B**
```powershell
ollama pull mistral
```
- Fast (5-8 sec per response)
- High quality  
- 4 GB VRAM needed
- 3.8 GB download

### 🔥 **Better Quality: Llama2 13B (if you want slower but smarter)**
```powershell
ollama pull llama2:13b
```
- Slower (10-12 sec per response)
- Even better quality
- 8-10 GB VRAM needed
- 7.3 GB download

**Wait for download to complete!** You'll see:
```
pulling manifest
pulling 5136cde6cbac
...
success
```

---

## ⚙️ Configure Tutoring Bot

Go to the tutor-bot-ollama folder and copy the config:

```powershell
cd C:\Users\stein\tutor-bot-ollama
copy .env.ollama .env
```

That's it! The `.env` already has:
```
LLM_PROVIDER=ollama
OLLAMA_LLM_MODEL=mistral
OLLAMA_BASE_URL=http://localhost:11434
```

---

## ▶️ Run It!

```powershell
# 1. Make sure you're in the project folder
cd C:\Users\stein\tutor-bot-ollama

# 2. Create virtual environment (first time only)
python -m venv .venv

# 3. Activate it
.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start Ollama server (in one PowerShell window)
ollama serve

# 6. Start tutoring bot (in another PowerShell window)
streamlit run app.py

# 7. Open browser to http://localhost:8501
```

---

## 💡 Tips

- **GPU working?** Responses should be 5-8 seconds. If >20 sec, check `nvidia-smi`
- **Slow?** Make sure `ollama serve` is running in a separate terminal
- **Change models?** Edit `.env` and change `OLLAMA_LLM_MODEL=neural-chat`
- **Want to switch back to ChatGPT?** Change `.env` to `LLM_PROVIDER=openai` and add your GITHUB_TOKEN

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Can't reach localhost:11434" | Run `ollama serve` in another terminal |
| "Model not found" | Run `ollama pull mistral` |
| Very slow (>20 sec) | Check GPU: `nvidia-smi` (should show RTX 5070) |
| Streamlit error | Refresh browser page, Ollama will auto-reconnect |

---

**🎉 You're ready! Start tutoring completely offline.**

For detailed info, see `OLLAMA_SETUP.md`
