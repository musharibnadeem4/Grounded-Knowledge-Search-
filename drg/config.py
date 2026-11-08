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
INDEX_META_FILE = "index_meta.json"  # how an index was built (e.g. context_header); inside INDEX_DIR
COLLECTION = "chunks"

# Chroma write batch size (its hard limit is ~5k)
CHROMA_BATCH = 2000

# Retrieval
# bge recommends a query instruction for retrieval; empty = embed the question as-is.
QUERY_PREFIX = ""
# Parse company / year from the question and narrow the Chroma filter (never widens the role filter).
YEAR_COMPANY_FILTER = True  # kept experiment (e2); set False to disable

# Optional cross-encoder reranker. None = off. The reranker only reorders candidates that
# the same Chroma query / where filter already returned (access control is unchanged).
RERANKERS_ALLOWED = ("cross-encoder/ms-marco-MiniLM-L-6-v2", "BAAI/bge-reranker-base")
RERANKER = None
RERANK_DEPTH = 50  # candidates fetched and reranked; at least k are always fetched

# Drop retrieved chunks whose stripped text is shorter than this many characters (0 = off).
# MIN_CHUNK_OVERFETCH x the usual candidate count is fetched so k results can still be returned.
MIN_CHUNK_CHARS = 0
MIN_CHUNK_OVERFETCH = 3
# Embed only the sentences that end with "?" or mention a parsed company / year
# (falls back to the whole question). Retrieval only; the original question is untouched.
QUERY_CLEAN = False
# Drop chunks under 80 characters and chunks from exhibit-index / signature pages
# (drg/boilerplate.py). DROP_BOILERPLATE_OVERFETCH x the usual candidate count is fetched.
DROP_BOILERPLATE = False
DROP_BOILERPLATE_OVERFETCH = 3
# When a company has both a 10k and a 10k_annualreport doc for the same period, exclude the
# annual-report doc in the where filter.
PREFER_10K_OVER_ANNUALREPORT = True

# ask
ASK_K = 8  # chunks given to the LLM for a question naming at most one company
ASK_K_PER_COMPANY = 6  # chunks retrieved for EACH company when a question names 2+ companies
LLM_TIMEOUT = 30  # seconds
# Provider / model come from the environment (.env): LLM_PROVIDER, LLM_MODEL. See .env.example.
