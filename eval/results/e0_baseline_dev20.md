# Eval run: e0_baseline_dev20

- Timestamp: 2026-11-08T16:55:20+05:00
- Git SHA: 248546b22bc1cf397e32efbc83453414303d1d9e (dirty)
- Question types: {'answerable': 20}
- **ACL leaks: 0** (must be 0)
- Search latency: p50 93 ms, p95 101 ms (n=20, retrieval depth 20, model load excluded)

## Overall (answerable questions)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 20 | 0.600 | 0.150 | 0.150 | 0.850 | 0.250 | 0.250 | 1.000 | 0.350 | 0.325 | 0.053 |

## By tag

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| multi_page | 4 | 0.750 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.250 | 0.125 | 0.000 |

## By doc_type (of gold doc)

| group | n | doc_hit@5 | page_hit@5 | gold_page_recall@5 | doc_hit@10 | page_hit@10 | gold_page_recall@10 | doc_hit@20 | page_hit@20 | gold_page_recall@20 | mrr@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k | 16 | 0.562 | 0.125 | 0.125 | 0.812 | 0.250 | 0.250 | 1.000 | 0.375 | 0.344 | 0.054 |
| 10q | 2 | 1.000 | 0.500 | 0.500 | 1.000 | 0.500 | 0.500 | 1.000 | 0.500 | 0.500 | 0.100 |
| Earnings | 2 | 0.500 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |

## Full config

```json
{
 "args": {
  "run_name": "e0_baseline_dev20",
  "k": [
   5,
   10,
   20
  ],
  "index_dir": "D:\\Assignment DRG\\index",
  "questions": "D:\\Assignment DRG\\eval\\questions.jsonl"
 },
 "drg.config": {
  "CACHE_DIR": "cache\\pages",
  "CHROMA_BATCH": "2000",
  "CHUNK_OVERLAP": "50",
  "CHUNK_TOKENS": "350",
  "COLLECTION": "chunks",
  "EMBED_BATCH": "64",
  "EMBED_MODEL": "BAAI/bge-small-en-v1.5",
  "HASHES_FILE": "hashes.json",
  "INDEX_DIR": "D:\\Assignment DRG\\index",
  "MANIFEST_PATH": "D:\\Assignment DRG\\manifest.csv",
  "MAX_CHUNK_TOKENS": "500",
  "QUERY_PREFIX": ""
 },
 "retrieved_depth": 20,
 "question_types": {
  "answerable": 20
 }
}
```
