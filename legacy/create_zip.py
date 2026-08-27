import shutil
import os
import zipfile
from pathlib import Path

output_file = "tutor-bot-project.zip"

# Remove old zip if exists
if os.path.exists(output_file):
    os.remove(output_file)
    print(f"Removed old {output_file}")

# Create zip with all files EXCEPT .venv, .chroma, .env, __pycache__, and large vector stores
def zipdir(path, ziph):
    count = 0
    skipped = 0
    for root, dirs, files in os.walk(path):
        # Skip directories - remove from dirs so os.walk doesn't descend into them
        skip_dirs = ['.venv', '__pycache__', '.chroma', '.git', '.pytest_cache', '.parquet', 'node_modules']
        
        # Also skip db/tutorial_* directories (Chroma stores) but keep db itself
        if root.endswith('db'):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('tutorial_')]
        else:
            dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            # Skip .env but keep .env.example
            if file == '.env':
                skipped += 1
                continue
            # Skip Python cache
            if file.endswith('.pyc'):
                skipped += 1
                continue
            # Skip Chroma parquet files
            if file.endswith('.parquet'):
                skipped += 1
                continue
            
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, '.')
            try:
                ziph.write(file_path, arcname)
                count += 1
            except Exception as e:
                print(f"Warning: Skipped {file_path}: {e}")
                skipped += 1
    
    return count, skipped

with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    file_count, skipped_count = zipdir('.', zipf)

# Verify
size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"\n✓ Created: {output_file}")
print(f"✓ Size: {size_mb:.2f} MB")
print(f"✓ Files included: {file_count}")
if skipped_count > 0:
    print(f"✓ Files skipped: {skipped_count} (Chroma, cache, .env)")

# List key files
print("\n📋 Key files in archive:")
with zipfile.ZipFile(output_file, 'r') as z:
    files = sorted(z.namelist())
    key_files = [f for f in files if any(x in f for x in [
        "README", 
        "app.py", 
        "metadata.json", 
        "requirements.txt", 
        "extract_tutorials",
        "process_with_llm",
        "transform_to_metadata"
    ])]
    for f in key_files:
        size = z.getinfo(f).file_size
        print(f"  • {f:<50} ({size:,} bytes)")

print("\n✓ Zip file ready for download at: tutor-bot-project.zip")
