import json
from pathlib import Path

# Load semantic chunks
chunks = []
with open("data/semantic_chunks.jsonl", "r") as f:
    for line in f:
        chunks.append(json.loads(line))

# Get unique document IDs (source_file_category format)
unique_ids = set()
for chunk in chunks:
    doc_id = f"{chunk['source_file']}_{chunk['category']}"
    unique_ids.add(doc_id)

print("Available Document IDs:")
print("=" * 50)
for doc_id in sorted(unique_ids):
    print(doc_id)
