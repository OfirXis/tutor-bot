# Learning Phase Redo: Master Plan

## Goal
Extract authoritative curriculum material from all 8 tutorials using ChatGPT 4o mini, then rebuild the topic lists and system prompt with verified, indexed learning material.

---

## Quick Start

### Step 1: Identify Your Materials
Read: **[STEP_0_LOCATE_MATERIALS.md](STEP_0_LOCATE_MATERIALS.md)**

**Questions to answer:**
- Do you have the 8 original PDF files? (List locations)
- If not, should we reconstruct from Chroma database?

**Action:**
```bash
# If reconstructing from Chroma:
python extract_from_chroma.py
# Output: db/curriculum_extraction/tutorial_{i}_reconstructed.txt (for i=1..8)
```

### Step 2: Follow the Pipeline
Read: **[LEARNING_PHASE_TODO.md](LEARNING_PHASE_TODO.md)**

**Phases:**
1. **Setup** — Create output directories and define extraction prompt
2. **Process** — Send each tutorial to ChatGPT 4o mini (8 calls)
3. **Extract** — Build indexed material (topics, algorithms, theorems)
4. **Validate** — Verify boundaries and prerequisites
5. **Integrate** — Update system with new curriculum

---

## Pipeline Overview

```
┌─ 8 Tutorials (PDF or reconstructed from Chroma)
│
├─→ ChatGPT 4o Mini (8 parallel or sequential calls)
│   Prompt: Extract concepts, algorithms, theorems, complexity
│
├─→ Parse Responses (8 JSON files)
│   - Topic lists
│   - Algorithm references
│   - Theorem references
│   - Complexity index
│
├─→ Build Cumulative Index
│   T1: 20 topics
│   T2: 26 topics (T1 + new)
│   T3: 26 topics (T2 + new)
│   ...
│   T8: 53+ topics (T7 + new)
│
├─→ Validate Boundaries
│   - No algorithm before first tutorial
│   - No theorem before introduction
│   - No cyclic prerequisites
│
├─→ Update Metadata
│   db/metadata.json → Replace topics arrays with ChatGPT-extracted ones
│
└─→ Test
    T1: Dijkstra blocked ✓
    T8: Dijkstra allowed ✓
```

---

## File Structure

**New directories created:**
```
db/
├── curriculum_extraction/
│   ├── extracted_material.json              (master curriculum data)
│   ├── topics_by_tutorial.json              (topic lists per tutorial)
│   ├── algorithms_reference.json            (all algorithms indexed)
│   ├── theorems_reference.json              (all theorems indexed)
│   ├── complexity_index.json                (all O-notation results)
│   ├── cumulative_topics_by_tutorial.json   (learning progression)
│   ├── raw_responses/                       (ChatGPT responses)
│   │   ├── tutorial_1_response.json
│   │   ├── tutorial_2_response.json
│   │   └── ... (8 total)
│   ├── tutorial_1_reconstructed.txt         (if extracted from Chroma)
│   ├── tutorial_2_reconstructed.txt
│   └── ... (if needed)
```

**Modified:**
```
db/
├── metadata.json                            (updated with new topics)
└── metadata_backup_old.json                 (backup of previous version)
```

---

## ChatGPT 4o Mini Extraction Prompt

Send this prompt to ChatGPT for **each tutorial**:

```
You are a curriculum analysis expert. I'm giving you tutorial material
for an algorithms course. Please analyze it carefully and extract:

1. CORE CONCEPTS (list all unique concepts introduced)
2. ALGORITHMS (name + brief description + complexity if mentioned)
3. THEOREMS & PROPERTIES (mathematical results, lemmas, proofs)
4. KEY EXAMPLES & PROBLEMS (important problem types covered)
5. COMPLEXITY ANALYSIS (all O-notation results)
6. LEARNING OBJECTIVES (what students should understand)
7. PREREQUISITES (what prior knowledge is required)
8. CONNECTIONS TO OTHER TOPICS (which topics relate to which)

Format your response as JSON with these sections:
{
  "tutorial_id": "<number>",
  "core_concepts": ["concept1", "concept2", ...],
  "algorithms": [
    {
      "name": "algorithm name",
      "description": "...",
      "time_complexity": "O(...)",
      "space_complexity": "O(...)",
      "prerequisites": ["concept1", ...]
    }
  ],
  "theorems": [
    {
      "name": "theorem name",
      "statement": "...",
      "applies_to": ["algorithm1", ...]
    }
  ],
  "complexity_results": [
    {"description": "...", "notation": "O(...)"}
  ],
  "learning_objectives": ["objective1", ...],
  "prerequisites": ["prior_topic1", ...]
}

Focus on accuracy. Only include what is actually taught, not general CS knowledge.
```

---

## Phase Breakdown

### Phase 1: Setup (Preparation)
- [ ] Locate/reconstruct all 8 tutorial materials
- [ ] Create output directory structure
- [ ] Finalize extraction prompt template

### Phase 2: Process (ChatGPT Calls)
- [ ] Send Tutorial 1 → ChatGPT → Save response
- [ ] Send Tutorial 2 → ChatGPT → Save response
- [ ] ... (repeat for all 8)
- [ ] Verify all 8 responses received

### Phase 3: Extract (Build Indices)
- [ ] Parse all 8 responses into structured format
- [ ] Build topic lists (cumulative)
- [ ] Build algorithm reference
- [ ] Build theorem reference
- [ ] Build complexity index

### Phase 4: Validate (Quality Check)
- [ ] No algorithms before introduction tutorial
- [ ] No theorems before teaching tutorial
- [ ] All prerequisites are learnable in order
- [ ] Topics don't overlap between tutorials

### Phase 5: Integrate (Deploy)
- [ ] Update metadata.json with new topics
- [ ] Restart Streamlit app
- [ ] Verify system works with new curriculum
- [ ] Run boundary tests (T1, T4, T8)

### Phase 6: QA (Testing)
- [ ] T1 blocks Dijkstra ✓
- [ ] T4 allows DP ✓
- [ ] T7 allows Kruskal ✓
- [ ] T8 allows everything ✓

### Phase 7: Archive
- [ ] Backup old metadata
- [ ] Clean temporary files
- [ ] Keep curriculum_extraction/ for reference

---

## Success Criteria

✓ All 8 tutorials processed by ChatGPT 4o mini  
✓ Topics extracted and cumulative lists built  
✓ No out-of-order topic references  
✓ Boundary enforcement working (tested)  
✓ System prompt uses verified curriculum  
✓ App running stable with new topics  

---

## Timeline Estimate

| Phase | Effort | Time |
|-------|--------|------|
| Phase 1 (Setup) | Low | ~15 min |
| Phase 2 (ChatGPT Calls) | Medium | ~30 min (manual ChatGPT interactions) |
| Phase 3 (Extract) | Medium | ~45 min (parsing + normalization) |
| Phase 4 (Validate) | Medium | ~30 min |
| Phase 5 (Integrate) | Low | ~15 min |
| Phase 6 (QA) | Low | ~20 min |
| **Total** | | ~2.5 hours |

---

## Next Action

1. **Read** [STEP_0_LOCATE_MATERIALS.md](STEP_0_LOCATE_MATERIALS.md) — Identify tutorial sources
2. **Prepare** — Extract or locate materials
3. **Read** [LEARNING_PHASE_TODO.md](LEARNING_PHASE_TODO.md) — Detailed task list
4. **Execute** — Follow each phase in order

---

## Questions?

- **Where are the PDFs?** → See STEP_0_LOCATE_MATERIALS.md
- **How do I send to ChatGPT?** → Use the extraction prompt template above
- **Can I automate this?** → ChatGPT integration can be scripted (Phase 2+)
- **What if a topic appears in multiple tutorials?** → List it in earliest tutorial, then include in cumulative for later ones

---

**Start here:** Identify your materials location, then follow the pipeline.
