#!/usr/bin/env python3
"""
Extract tutorial materials from Chroma vector database.
Use this if original PDFs are unavailable.
Reconstructs curriculum content from stored chunks.
"""

import json
from pathlib import Path
import chromadb

def extract_all_tutorials():
    """Extract all 8 tutorials from Chroma and save as JSON."""
    
    client = chromadb.PersistentClient(path="db")
    output_dir = Path("db/curriculum_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_tutorials = {}
    
    print("=" * 80)
    print("EXTRACTING TUTORIALS FROM CHROMA DATABASE")
    print("=" * 80)
    print()
    
    for i in range(1, 9):
        collection_name = f"tutorial_{i}_chunks"
        print(f"Tutorial {i}: Querying collection '{collection_name}'...", end=" ")
        
        try:
            collection = client.get_collection(name=collection_name)
            results = collection.get(include=["documents", "metadatas"])
            
            chunks = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            
            # Reconstruct content
            tutorial_data = {
                "tutorial_id": i,
                "chunks_count": len(chunks),
                "chunks": []
            }
            
            for j, (doc, meta) in enumerate(zip(chunks, metadatas), 1):
                tutorial_data["chunks"].append({
                    "chunk_id": j,
                    "content": doc,
                    "metadata": meta
                })
            
            all_tutorials[f"tutorial_{i}"] = tutorial_data
            print(f"✓ {len(chunks)} chunks extracted")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            all_tutorials[f"tutorial_{i}"] = {
                "error": str(e),
                "chunks": []
            }
    
    print()
    print("=" * 80)
    
    # Save master file
    output_file = output_dir / "chroma_extraction_raw.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tutorials, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {output_file}")
    
    # Save individual reconstructed texts for ChatGPT
    print()
    print("Creating plaintext reconstructions for ChatGPT...")
    
    for i in range(1, 9):
        tutorial_key = f"tutorial_{i}"
        if tutorial_key not in all_tutorials:
            continue
        
        tutorial = all_tutorials[tutorial_key]
        
        if "error" in tutorial:
            print(f"  Tutorial {i}: Skipped (error)")
            continue
        
        # Reconstruct as plaintext
        text_content = f"# Tutorial {i}\n\n"
        for chunk in tutorial["chunks"]:
            text_content += f"## Chunk {chunk['chunk_id']}\n"
            text_content += chunk["content"]
            text_content += "\n\n"
        
        text_file = output_dir / f"tutorial_{i}_reconstructed.txt"
        text_file.write_text(text_content, encoding='utf-8')
        print(f"  Tutorial {i}: Saved {len(tutorial['chunks'])} chunks")
    
    print()
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review reconstructed files in: db/curriculum_extraction/")
    print("2. Send each tutorial_{i}_reconstructed.txt to ChatGPT 4o mini")
    print("3. Store responses in: db/curriculum_extraction/raw_responses/")
    print()

if __name__ == "__main__":
    extract_all_tutorials()
