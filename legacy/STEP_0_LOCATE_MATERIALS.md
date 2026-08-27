# Step 0: Locate Tutorial Source Files

Before starting Phase 1 of the pipeline, we need to identify all 8 tutorial materials.

## Current Status Check

### [ ] Where are the tutorial materials?
The current system uses Chroma vector database with embedded chunks. We need to extract/locate the original source.

**Questions to Answer:**

1. **[ ] Do we have the 8 original PDF files?**
   - [ ] Tutorial 1 PDF location: ___________________
   - [ ] Tutorial 2 PDF location: ___________________
   - [ ] Tutorial 3 PDF location: ___________________
   - [ ] Tutorial 4 PDF location: ___________________
   - [ ] Tutorial 5 PDF location: ___________________
   - [ ] Tutorial 6 PDF location: ___________________
   - [ ] Tutorial 7 PDF location: ___________________
   - [ ] Tutorial 8 PDF location: ___________________

2. **[ ] If PDFs don't exist, can we extract from Chroma?**
   - Current Chroma databases contain: `db/tutorial_1/`, `db/tutorial_2/`, ..., `db/tutorial_8/`
   - Each has embedded chunks (max 15 per tutorial)
   - Plan: Query Chroma to retrieve all chunks, reconstruct tutorial content
   - Would lose formatting but gain original curriculum text

3. **[ ] Alternative: Do we have source documents?**
   - Course slides (PowerPoint/PDF)?
   - Course notes (Markdown/Word)?
   - Textbook chapters?
   - Course website content?

---

## Action Items

### [ ] 0.1 Locate All Tutorial Materials
- **ACTION**: Find and list all 8 tutorial source files
- **EVIDENCE**: Provide file paths or URLs

### [ ] 0.2 If Materials Missing: Reconstruct from Chroma
- **SCRIPT NEEDED**: Create `extract_from_chroma.py`
  - Query each tutorial's Chroma DB
  - Export all chunks (≤15 per tutorial)
  - Save as: `db/curriculum_extraction/reconstructed_tutorial_{i}.txt`
  - Allows ChatGPT to analyze reconstructed content

### [ ] 0.3 Prepare Materials for ChatGPT
- **FORMAT**: PDF or plaintext?
- **SIZE**: Check file sizes (ChatGPT has context limits)
- **READINESS**: Ensure all 8 materials are accessible before Phase 1

---

## If Reconstructing from Chroma

### Script: `extract_from_chroma.py`
```python
import chromadb
from pathlib import Path

client = chromadb.PersistentClient(path="db")

for i in range(1, 9):
    collection_name = f"tutorial_{i}_chunks"
    try:
        collection = client.get_collection(name=collection_name)
        results = collection.get(include=["documents", "metadatas"])
        
        # Reconstruct content
        content = f"# Tutorial {i}\n\n"
        for j, doc in enumerate(results['documents'], 1):
            content += f"## Chunk {j}\n{doc}\n\n"
        
        # Save
        output_file = f"db/curriculum_extraction/reconstructed_tutorial_{i}.txt"
        Path(output_file).write_text(content)
        print(f"✓ Tutorial {i}: {len(results['documents'])} chunks extracted")
    except Exception as e:
        print(f"✗ Tutorial {i}: {e}")
```

**TO DO**: [ ] Create this script when materials cannot be located

---

## Next Step
**→ Once materials are located/reconstructed, proceed to LEARNING_PHASE_TODO.md Phase 1**
