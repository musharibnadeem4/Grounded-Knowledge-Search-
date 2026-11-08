"""Tunable settings. Change chunk sizes here to run experiments."""
from pathlib import Path

# Chunking (token counts use the embedding model's tokenizer)
CHUNK_TOKENS = 350
CHUNK_OVERLAP = 50
MAX_CHUNK_TOKENS = 500  # hard cap, counted with special tokens

# Embedding
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_BATCH = 64

# Paths (relative to the working directory)
MANIFEST_PATH = Path("manifest.csv")
CACHE_DIR = Path("cache") / "pages"
INDEX_DIR = Path("index")
HASHES_FILE = "hashes.json"  # lives inside INDEX_DIR
COLLECTION = "chunks"

# Chroma write batch size (its hard limit is ~5k)
CHROMA_BATCH = 2000
