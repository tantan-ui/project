import ollama
from docx import Document
from pinecone import Pinecone
import os


PINECONE_API_KEY = "pcsk_PWCyW_9yXZKtkDkHkuVKCquoxCXwkqncYZJL3qiktMQALzGrh56pUYZMu733HNJAoNAa6"


INDEX_NAME = "context"
MODEL_NAME = "nomic-embed-text"  
DOC_FILE = "Context.docx"

# --- SETUP ---
# 1. Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# 2. Helper to extract text
def extract_text(file_path):
    if not os.path.exists(file_path):
        # Fallback: check if file is in the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, os.path.basename(file_path))
        
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text])

# 3. Helper to chunk text
def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# 4. Generate Embeddings using Ollama (Batched for speed)
def get_embeddings(chunks):
    if not chunks:
        return []
    
    # Use ollama.embed with the 'input' list for batch processing
    response = ollama.embed(model=MODEL_NAME, input=chunks)
    return response["embeddings"]

# --- EXECUTION ---
try:
    print(f"Reading {DOC_FILE}...")
    raw_text = extract_text(DOC_FILE)
    
    if not raw_text.strip():
        raise ValueError("Document appears to be empty.")

    print("Chunking text...")
    chunks = chunk_text(raw_text)
    print(f"Created {len(chunks)} chunks.")

    print(f"Generating embeddings with Ollama ({MODEL_NAME})...")
    vectors = get_embeddings(chunks)

    # Prepare upsert payload
    vectors_to_upsert = [
        {"id": f"policy-chunk-{i}", "values": vec, "metadata": {"source": DOC_FILE, "chunk_index": i}}
        for i, vec in enumerate(vectors)
    ]

    print(f"Upserting {len(vectors_to_upsert)} vectors to Pinecone index '{INDEX_NAME}'...")
    index.upsert(vectors=vectors_to_upsert)
    
    print("✅ Document upserted successfully using free local embeddings!")

except Exception as e:
    print(f"❌ Error: {e}")   