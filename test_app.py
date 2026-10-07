import streamlit as st
import os
from pathlib import Path

st.write("Step 1: Importing modules...")

try:
    import rag_engine as rag
    st.write("✓ rag_engine imported")
except Exception as e:
    st.error(f"✗ rag_engine failed: {e}")
    st.stop()

try:
    from curriculum import CURRICULUM_FILE, course_name
    st.write("✓ curriculum imported")
except Exception as e:
    st.error(f"✗ curriculum failed: {e}")
    st.stop()

try:
    from local_models import HEBREW_MODELS, TRANSLATION_MODELS, TUTOR_MODELS, model_options, model_label
    st.write("✓ local_models imported")
except Exception as e:
    st.error(f"✗ local_models failed: {e}")
    st.stop()

try:
    from homework_material import (
        homework_pdf_path, homework_clarification, selected_statements,
        problem_numbers, resolve_homework_followup, homework_content_request, homework_overview_answer,
    )
    st.write("✓ homework_material imported")
except Exception as e:
    st.error(f"✗ homework_material failed: {e}")
    st.stop()

st.write("Step 2: Loading metadata...")

try:
    os.chdir(Path(__file__).parent)
    meta = rag.load_meta()
    st.write(f"✓ Loaded meta with {len(meta)} tutorials")
except Exception as e:
    st.error(f"✗ load_meta failed: {e}")
    import traceback
    st.text(traceback.format_exc())
    st.stop()

try:
    homework = rag.load_homework()
    st.write(f"✓ Loaded homework with {len(homework)} assignments")
except Exception as e:
    st.error(f"✗ load_homework failed: {e}")
    import traceback
    st.text(traceback.format_exc())
    st.stop()

try:
    retriever = rag.HybridRetriever()
    st.write(f"✓ Loaded retriever with {len(retriever.chunks)} chunks")
except Exception as e:
    st.error(f"✗ HybridRetriever failed: {e}")
    import traceback
    st.text(traceback.format_exc())
    st.stop()

st.write("✓ All imports and data loading successful!")
