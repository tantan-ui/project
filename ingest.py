
import argparse
import os
import sys
import ollama
from docx import Document
from pinecone import Pinecone

# Default configuration fallback
DEFAULT_PINECONE_API_KEY = "pcsk_PWCyW_9yXZKtkDkHkuVKCquoxCXwkqncYZJL3qiktMQALzGrh56pUYZMu733HNJAoNAa6"
DEFAULT_INDEX_NAME = "context"
DEFAULT_MODEL_NAME = "nomic-embed-text"  

def extract_text(file_path):
    """Extracts text from a .docx file."""
    if not os.path.exists(file_path):
        # Fallback: check if file is in the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, os.path.basename(file_path))
        
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        print(f"❌ Error reading document: {e}", file=sys.stderr)
        sys.exit(1)

def chunk_text(text, chunk_size):
    """Splits text into chunks of specified character length."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_embeddings(chunks, model_name):
    """Generates embeddings using Ollama."""
    if not chunks:
        return []
    try:
        response = ollama.embed(model=model_name, input=chunks)
        return response["embeddings"]
    except Exception as e:
        print(f"❌ Ollama Error: {e}", file=sys.stderr)
        print("💡 Make sure Ollama is running and the model is pulled (`ollama pull nomic-embed-text`).", file=sys.stderr)
        sys.exit(1)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="CLI tool to chunk a .docx file, generate embeddings via Ollama, and upsert to Pinecone."
    )
    
    # Required arguments
    parser.add_argument(
        "file", 
        help="Path to the .docx file to ingest"
    )
    
    # Optional arguments with your original defaults
    parser.add_argument(
        "-i", "--index", 
        default=DEFAULT_INDEX_NAME,
        help=f"Pinecone index name (default: {DEFAULT_INDEX_NAME})"
    )
    parser.add_argument(
        "-c", "--chunk-size", 
        type=int, 
        default=500,
        help="Character size for text chunking (default: 500)"
    )
    parser.add_argument(
        "-m", "--model", 
        default=DEFAULT_MODEL_NAME,
        help=f"Ollama embedding model (default: {DEFAULT_MODEL_NAME})"
    )
    parser.add_argument(
        "-k", "--key", 
        default=os.environ.get("PINECONE_API_KEY", DEFAULT_PINECONE_API_KEY),
        help="Pinecone API Key (defaults to hardcoded key or PINECONE_API_KEY env variable)"
    )

    args = parser.parse_args()

    try:
        print(f"📋 Reading {args.file}...")
        raw_text = extract_text(args.file)
        
        if not raw_text.strip():
            print("❌ Error: Document appears to be empty.", file=sys.stderr)
            sys.exit(1)

        print(f"✂️  Chunking text into blocks of {args.chunk_size} characters...")
        chunks = chunk_text(raw_text, args.chunk_size)
        print(f"🧩 Created {len(chunks)} chunks.")

        print(f"🤖 Generating embeddings with Ollama ({args.model})...")
        vectors = get_embeddings(chunks, args.model)

        print(f"⚙️  Initializing Pinecone client...")
        pc = Pinecone(api_key=args.key)
        index = pc.Index(args.index)

        # Prepare upsert payload using file basename for metadata clean up
        file_basename = os.path.basename(args.file)
        vectors_to_upsert = [
            {"id": f"policy-chunk-{i}", "values": vec, "metadata": {"source": file_basename, "chunk_index": i}}
            for i, vec in enumerate(vectors)
        ]

        print(f"🚀 Upserting {len(vectors_to_upsert)} vectors to Pinecone index '{args.index}'...")
        index.upsert(vectors=vectors_to_upsert)
        
        print("✅ Document upserted successfully using free local embeddings!")

    except Exception as e:
        print(f"❌ Critical Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()