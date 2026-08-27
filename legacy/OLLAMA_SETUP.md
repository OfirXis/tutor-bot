# 🤖 Ollama Setup Guide — Tutoring Bot with Local LLM

This guide will help you set up Ollama and the tutoring bot to run **completely offline** using your NVIDIA GPU.

---

## 📋 Quick Summary

**Your Hardware:** 
- ✅ 32 GB RAM (excellent)
- ✅ NVIDIA RTX 5070 Laptop GPU with 4 GB VRAM (great for local models)
- ✅ Windows 11
- ✅ 1500+ GB free disk space

**Recommendation:**
- **Best:** Mistral 7B (fast & quality, ~5-8 sec per response, 5 GB VRAM needed)
- **Alternative:** Llama2 13B (slower but better quality, ~10-12 sec, 10 GB VRAM needed)
- **Size:** ~3.8-7.5 GB depending on model

---

## ⚡ Step 1: Install Ollama

### Windows Installation

1. **Download Ollama for Windows:**
   - Visit: https://ollama.ai/download/windows
   - Download the installer (OllamaSetup.exe)
   - Run it and follow the installation wizard
   - **✓ Default location:** `C:\Users\[YourName]\AppData\Local\Programs\Ollama`

2. **Verify Installation:**
   ```powershell
   ollama --version
   # Should display: ollama version 0.x.x
   ```

3. **Initial Setup:**
   - After installation, Ollama will start automatically
   - You should see it running in the system tray (check bottom-right of taskbar)
   - It will be accessible at `http://localhost:11434`

---

## 🎯 Step 2: Pull Your Model

Choose one model from below and run the command in PowerShell:

### Option A: Mistral 7B ⭐ Recommended
```powershell
ollama pull mistral
```
- **Size:** ~3.8 GB (after quantization)
- **Speed:** 5-8 seconds per response
- **Quality:** Excellent
- **VRAM:** 4-5 GB
- **First download:** ~2-3 minutes on fast internet

### Option B: Neural Chat 7B (Also Great!)
```powershell
ollama pull neural-chat
```
- **Size:** ~3.9 GB
- **Speed:** 6-10 seconds per response
- **Quality:** Excellent for dialogue
- **VRAM:** 4-5 GB

### Option C: Llama2 13B (Best Quality, Slower)
```powershell
ollama pull llama2:13b
```
- **Size:** ~7.3 GB
- **Speed:** 8-12 seconds per response
- **Quality:** Even better than Mistral
- **VRAM:** 8-10 GB
- **First download:** ~5-8 minutes

### Option D: Dolphin Mixtral 7B (Creative)
```powershell
ollama pull dolphin-mixtral
```
- **Size:** ~7.5 GB
- **Speed:** 7-10 seconds per response
- **Quality:** Very high, more creative
- **VRAM:** 5-7 GB

**⏱️ Pulling takes time — be patient! The download happens only once.**

**Check if pull is complete:**
```powershell
ollama list
# Should show your model with size
```

---

## 🚀 Step 3: Configure the Tutoring Bot

### Option A: Use the Pre-Configured .env File

1. **Go to project folder:**
   ```powershell
   cd C:\Users\stein\tutor-bot-ollama
   ```

2. **Copy the Ollama config (we already created this for you):**
   ```powershell
   copy .env.ollama .env
   ```

3. **Verify `.env` contains:**
   ```
   LLM_PROVIDER=ollama
   OLLAMA_LLM_MODEL=mistral
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Option B: Manual Configuration

1. If `.env` doesn't exist, create it:
   ```powershell
   # In the project folder
   $env_content = @"
   LLM_PROVIDER=ollama
   OLLAMA_LLM_MODEL=mistral
   OLLAMA_BASE_URL=http://localhost:11434
   "@
   Set-Content -Path ".env" -Value $env_content
   ```

2. **To use a different model,** edit `.env` and change:
   ```
   OLLAMA_LLM_MODEL=llama2:13b
   # or
   OLLAMA_LLM_MODEL=neural-chat
   # etc.
   ```

---

## 🎓 Step 4: Run the Tutoring Bot

### Make Sure Ollama is Running

Check that Ollama server is active:
```powershell
# Test if Ollama is running
Invoke-WebRequest -Uri http://localhost:11434/api/tags -UseBasicParsing
# Should return your model info (if returns error, Ollama isn't running)

# If Ollama isn't running, start it:
ollama serve
```

### Start the Tutoring Bot

1. **Create virtual environment (first time only):**
   ```powershell
   cd C:\Users\stein\tutor-bot-ollama
   python -m venv .venv
   ```

2. **Activate it:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Start the app:**
   ```powershell
   streamlit run app.py
   ```

5. **Open in browser:**
   - Automatic popup should appear
   - Or visit: http://localhost:8501

6. **Start tutoring:**
   - Select a tutorial from the dropdown
   - Ask a question
   - Watch Ollama generate responses locally! 🎉

---

## ⚙️ GPU Acceleration (CUDA)

Your NVIDIA GPU should work automatically, but verify:

### Check GPU Support

```powershell
# See if GPU is being used
ollama list
# Look for model details

# Test with a simple query to see if GPU is active
ollama run mistral "What is 2+2?"
# Should be fast (GPU working) not slow (CPU-only)
```

### Troubleshooting GPU Issues

If responses are very slow (>20 seconds), GPU might not be accelerating:

1. **Ensure NVIDIA Drivers are Updated:**
   ```powershell
   # Check NVIDIA driver version
   nvidia-smi
   # Should show your RTX 5070 and CUDA version
   ```

2. **CUDA Toolkit (if GPU not accelerating):**
   - Ollama usually handles this automatically
   - If needed, download from: https://developer.nvidia.com/cuda-toolkit
   - Download the latest version (12.1+)

3. **Restart Ollama to reset GPU:**
   ```powershell
   # Stop Ollama service
   Stop-Process -Name ollama
   # Wait a few seconds
   Start-Sleep -Seconds 3
   # Start it again
   ollama serve
   ```

---

## 📊 Performance Expectations

### Mistral 7B (Recommended)
| Task | Time | GPU Usage |
|------|------|-----------|
| First response (model load) | ~3-5 sec | 100% |
| Typical response | 5-8 sec | 95%+ |
| Memory used | 4-5 GB VRAM | |

### Llama2 13B (If you want better quality)
| Task | Time | GPU Usage |
|------|------|-----------|
| First response | ~5-8 sec | 100% |
| Typical response | 10-12 sec | 95%+ |
| Memory used | 8-10 GB VRAM | |

### CPU-Only (if GPU fails)
- Mistral: 30-60 seconds per response
- Llama2: 60-120 seconds per response
- ⚠️ Much slower — GPU acceleration is important!

---

## 🔧 Troubleshooting

### Problem: "Connection refused" error
```
Error: Can't reach http://localhost:11434
```
**Solution:**
1. Check that Ollama server is running:
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*ollama*"}
   ```
2. If not found, start it:
   ```powershell
   ollama serve
   ```
3. Wait 5 seconds and retry

### Problem: "Model not found" error
```
Error: model 'mistral' not found
```
**Solution:**
1. Download the model:
   ```powershell
   ollama pull mistral
   ```
2. Verify it was downloaded:
   ```powershell
   ollama list
   ```
3. Restart the tutoring bot

### Problem: Very slow responses (>20 seconds)
**GPU is probably not accelerating. Try:**
1. Check GPU availability:
   ```powershell
   nvidia-smi
   ```
2. Restart Ollama and bot:
   ```powershell
   Stop-Process -Name ollama
   Start-Sleep -Seconds 3
   ollama serve  # in another terminal
   # Then restart streamlit in another terminal
   ```
3. Check Ollama logs for errors

### Problem: High RAM usage or crashes
**The model might be too large.** Try:
1. Switch to a smaller model:
   ```powershell
   # Stop bot
   # Edit .env: OLLAMA_LLM_MODEL=mistral
   # Restart bot
   ```
2. Pull the model first:
   ```powershell
   ollama pull mistral
   ```

### Problem: Streamlit shows error "LLM failed"
**Ollama server might not be responding.** Try:
1. Check Ollama is running:
   ```powershell
   curl http://localhost:11434/api/tags
   ```
2. If error, restart Ollama:
   ```powershell
   Stop-Process -Name ollama
   ollama serve
   ```
3. Refresh the browser page (Streamlit auto-reconnects)

---

## 💡 Tips & Tricks

### Test Model Before Starting Tutoring Bot
```powershell
ollama run mistral "Explain the merge sort algorithm briefly"
```
- Fast response? GPU is working
- Slow response? Consider checking GPU setup

### See What's Running
```powershell
# Check Ollama process
Get-Process | Where-Object {$_.ProcessName -like "*ollama*"}

# Check if port 11434 is active
netstat -ano | findstr ":11434"
```

### Switch Models Quickly
1. Edit `.env`:
   ```
   OLLAMA_LLM_MODEL=llama2:13b
   ```
2. Reload Streamlit (browser refresh)
3. Model will auto-switch

### Clean Up Old Models
```powershell
# List all models
ollama list

# Delete a model if needed
ollama rm mistral
```

---

## 🎯 Next Steps

1. ✅ Install Ollama
2. ✅ Pull a model (mistral recommended)
3. ✅ Configure `.env` with LLM_PROVIDER=ollama
4. ✅ Create virtual environment
5. ✅ Install dependencies
6. ✅ Start tutoring bot
7. ✅ Begin tutoring completely offline!

---

## 📚 Additional Resources

- **Ollama Official:** https://ollama.ai
- **Model Library:** https://ollama.ai/library
- **Troubleshooting:** https://github.com/ollama/ollama/issues
- **NVIDIA CUDA:** https://developer.nvidia.com/cuda-toolkit

---

## ❓ FAQ

**Q: Is Ollama free?**
A: Yes, completely free and open-source.

**Q: Does everything run offline?**
A: Yes! After downloading the model, everything runs locally on your computer.

**Q: Can I switch back to ChatGPT?**
A: Yes, just change `LLM_PROVIDER=openai` in `.env` and add your GITHUB_TOKEN or OPENAI_API_KEY.

**Q: Which model should I start with?**
A: Try Mistral 7B first. If it's not smart enough, try Llama2 13B.

**Q: How do I know if GPU is working?**
A: Responses should come in 5-8 seconds. If >20 seconds, check nvidia-smi.

**Q: Can I use this on CPU only?**
A: Yes, but it will be very slow (30-120+ seconds per response).

---

**Happy learning! 🚀** Your tutoring bot is now ready to run completely offline with local AI.
