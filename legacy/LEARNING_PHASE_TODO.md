# Learning Phase Pipeline: ChatGPT 4o Mini Extraction

## Objective
Process all 8 tutorials via ChatGPT 4o mini to extract and index curriculum material by tutorial number.

---

## PHASE 1: Setup & Preparation

### [ ] 1.1 Collect All Tutorial PDFs
- [ ] Locate PDF for Tutorial 1 (Intro to Algorithm Analysis)
- [ ] Locate PDF for Tutorial 2 (Divide and Conquer)
- [ ] Locate PDF for Tutorial 3 (Greedy Algorithms)
- [ ] Locate PDF for Tutorial 4 (Dynamic Programming)
- [ ] Locate PDF for Tutorial 5 (DP Part 2)
- [ ] Locate PDF for Tutorial 6 (DP Part 3)
- [ ] Locate PDF for Tutorial 7 (Minimum Spanning Trees)
- [ ] Locate PDF for Tutorial 8 (Shortest Paths)
- **Output**: List of 8 PDF file paths

### [ ] 1.2 Create Output Structure
- [ ] Create folder: `db/curriculum_extraction/`
- [ ] Create file: `db/curriculum_extraction/extracted_material.json` (master index)
- [ ] Create folder: `db/curriculum_extraction/raw_responses/` (store ChatGPT responses)
- **Output**: Directory structure ready for extracted content

### [ ] 1.3 Define Extraction Prompt Template
- [ ] Create prompt for ChatGPT 4o mini that asks to extract:
  - Main concepts covered
  - Algorithms introduced
  - Theorems/properties
  - Key examples
  - Problem types
  - Prerequisites (what prior knowledge is needed)
  - Complexity classes (time/space)
- **Output**: Reusable prompt template

---

## PHASE 2: Process Each Tutorial (Tutorial 1-8)

### For Each Tutorial:

#### [ ] 2.1 Extract Tutorial i (where i = 1 to 8)

**Subtasks for Tutorial i:**

- [ ] **2.1.1** Read PDF file: `tutorial_{i}.pdf`
- [ ] **2.1.2** Convert PDF to text (extract readable content)
- [ ] **2.1.3** Send to ChatGPT 4o mini with extraction prompt:
  ```
  "Please analyze this algorithms course material and extract:
   1. Core concepts (list each concept)
   2. Algorithms introduced (name + brief description)
   3. Theorems or mathematical properties
   4. Example problems and solutions
   5. Complexity analysis (O-notation results)
   6. Learning objectives
   7. Prerequisites (what prior knowledge required)
   
   Format as structured JSON."
  ```
- [ ] **2.1.4** Receive structured response from ChatGPT
- [ ] **2.1.5** Validate extraction quality:
  - All algorithms mentioned?
  - All key concepts captured?
  - Complexity results accurate?
- [ ] **2.1.6** Store raw response: `db/curriculum_extraction/raw_responses/tutorial_{i}_response.json`
- [ ] **2.1.7** Parse & normalize response into standard format

**Repeat for i = 1, 2, 3, 4, 5, 6, 7, 8**

**Output**: 8 structured JSON files, one per tutorial

---

## PHASE 3: Build Cumulative Index

### [ ] 3.1 Create Master Index File
- [ ] Start with Tutorial 1 material
- [ ] Add Tutorial 2 material (appended to T1)
- [ ] Add Tutorial 3 material (appended to T1+T2)
- [ ] Continue through Tutorial 8
- **Purpose**: Track cumulative learning at each stage
- **Output**: `db/curriculum_extraction/cumulative_topics_by_tutorial.json`
  
  ```json
  {
    "tutorial_1": {
      "new_topics": ["Big-O", "asymptotic notation", ...],
      "all_topics_so_far": ["Big-O", "asymptotic notation", ...]
    },
    "tutorial_2": {
      "new_topics": ["divide and conquer", "merge sort", ...],
      "all_topics_so_far": ["Big-O", ..., "divide and conquer", "merge sort", ...]
    },
    ...
    "tutorial_8": {
      "new_topics": ["Dijkstra", "shortest path", ...],
      "all_topics_so_far": [... all 53+ topics ...]
    }
  }
  ```

---

## PHASE 4: Extract Key Learning Material

### [ ] 4.1 Build Topic List Per Tutorial
- [ ] Extract topic names from each tutorial's ChatGPT response
- [ ] Normalize topic names (consistency across tutorials)
- [ ] Create cumulative lists (T1-only, T1+T2, ..., T1-T8)
- **Output**: `db/curriculum_extraction/topics_by_tutorial.json`

### [ ] 4.2 Build Algorithm Reference
- [ ] Extract all algorithms mentioned per tutorial
- [ ] Include: name, complexity, prerequisites, first tutorial appearance
- [ ] Create indexed reference: `db/curriculum_extraction/algorithms_reference.json`
  
  ```json
  {
    "insertion_sort": {
      "first_tutorial": 1,
      "complexity_time": "O(n²)",
      "complexity_space": "O(1)",
      "prerequisites": ["Big-O notation", "loops"]
    },
    "dijkstra": {
      "first_tutorial": 8,
      "complexity_time": "O((V+E) log V)",
      "complexity_space": "O(V)",
      "prerequisites": ["graphs", "greedy", "shortest path"]
    }
  }
  ```

### [ ] 4.3 Build Theorem/Property Reference
- [ ] Extract mathematical theorems per tutorial
- [ ] Build index: `db/curriculum_extraction/theorems_reference.json`
  
  ```json
  {
    "master_theorem": {
      "first_tutorial": 2,
      "statement": "T(n) = aT(n/b) + f(n)",
      "applies_to": ["divide and conquer"]
    },
    ...
  }
  ```

### [ ] 4.4 Build Complexity Classes Index
- [ ] Extract all O-notation results per tutorial
- [ ] Build reference: `db/curriculum_extraction/complexity_index.json`

---

## PHASE 5: Validate & Integrate

### [ ] 5.1 Cross-Reference Validation
- [ ] Verify no algorithms mentioned before their intro tutorial
- [ ] Verify no theorems referenced before they're taught
- [ ] Verify prerequisites chain is valid (no circular dependencies)
- **Output**: Validation report

### [ ] 5.2 Compare with Current Metadata
- [ ] Compare extracted topics with current `db/metadata.json`
- [ ] Identify gaps in current curriculum
- [ ] Identify extra topics that should be removed/moved
- **Output**: Diff/reconciliation report

### [ ] 5.3 Update Metadata
- [ ] Decide: replace old `topics` lists with ChatGPT-extracted ones
- [ ] Update `db/metadata.json` with new canonical topics
- [ ] Or keep both versions for comparison
- **Output**: Updated `db/metadata.json`

---

## PHASE 6: Quality Assurance

### [ ] 6.1 Boundary Testing
- [ ] Test Tutorial 1: Verify Dijkstra is blocked
- [ ] Test Tutorial 4: Verify DP concepts work, MST blocked
- [ ] Test Tutorial 7: Verify Kruskal works, Dijkstra blocked
- [ ] Test Tutorial 8: Verify all topics accessible
- **Output**: Test results log

### [ ] 6.2 Topic Gate Validation
- [ ] Verify system prompt uses new topic lists correctly
- [ ] Verify LLM respects boundaries
- [ ] Check for any out-of-scope knowledge leakage
- **Output**: Validation checklist (✅/❌)

### [ ] 6.3 Documentation
- [ ] Document all extracted topics per tutorial
- [ ] Create learning path diagram (T1 → T2 → ... → T8)
- [ ] Document prerequisites for each major algorithm
- **Output**: Learning path documentation

---

## PHASE 7: Final Integration

### [ ] 7.1 Deploy New Curriculum
- [ ] Replace old `topics` arrays with ChatGPT-extracted ones
- [ ] Restart Streamlit app
- [ ] Verify app still works with new topics
- **Output**: App running with new curriculum

### [ ] 7.2 Archive Old Data
- [ ] Backup old `db/metadata.json` → `db/metadata_backup_old.json`
- [ ] Backup old Chroma databases (if needed)
- **Output**: Backup files created

### [ ] 7.3 Cleanup
- [ ] Remove temporary files
- [ ] Keep `db/curriculum_extraction/` folder for reference
- **Output**: Clean workspace

---

## Deliverables Summary

| File | Purpose | Status |
|------|---------|--------|
| `db/curriculum_extraction/extracted_material.json` | Master curriculum data | [ ] |
| `db/curriculum_extraction/topics_by_tutorial.json` | Topic lists (T1-T8) | [ ] |
| `db/curriculum_extraction/algorithms_reference.json` | Algorithm index | [ ] |
| `db/curriculum_extraction/theorems_reference.json` | Theorem index | [ ] |
| `db/curriculum_extraction/cumulative_topics_by_tutorial.json` | Learning progression | [ ] |
| `db/metadata.json` | Updated with new topics | [ ] |
| Validation report | Boundary testing results | [ ] |

---

## Notes
- **Tool**: ChatGPT 4o mini (via GitHub Copilot API)
- **Input**: 8 PDF tutorial files
- **Output**: Structured, indexed curriculum material
- **Goal**: Replace manual topic lists with AI-extracted authoritative curriculum
