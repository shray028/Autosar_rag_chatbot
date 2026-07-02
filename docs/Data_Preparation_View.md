# GR4ML — Data Preparation View

## AUTOSAR Document Intelligence Assistant

---

## Data Preparation View Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                  │
│   ████████████████████████████████████                                                                           │
│   █  Data Preparation View           █                                                                           │
│   ████████████████████████████████████                                                                           │
│                                                                                                                  │
│                                                                                                                  │
│  ┌──────────────────────────────────┐                                                  ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐   │
│  │ AUTOSAR Document Chunk           │                                ...               │  CHUNK_SIZE = 512   │   │
│  │ (Entity)                         │                                 │    ...         │  CHUNK_OVERLAP = 50 │   │
│  │──────────────────────────────────│          ┌──────────┐   ┌───────┴──┐  │          │  WHERE token_count>0│   │
│  │ - chunk_id  (PK)                 │ outputs  │  PDF     │   │ Semantic │  │          └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘   │
│  │ - document_name                  │◄╌╌╌╌╌╌╌╌╌│ Parsing  │──►│ Chunking │──┤               (Note)               │
│  │ - page_number                    │          │(Operator)│   │(Operator)│  │                                    │
│  │ - page_end                       │          └────┬─────┘   └──────────┘  │                                    │
│  │ - section_heading                │               │                       │                                    │
│  │ - chunk_text                     │               ▲                       ▼                                    │
│  │ - requirement_ids                │               │             ┌──────────────┐     ┌──────────────┐          │
│  │ - token_count                    │               │             │  Embedding   │────►│  Metadata    │          │
│  │ - embedding_vector (768-dim)     │           Data flow         │  Generation  │     │  Enrichment  │          │
│  │   ...                            │         (solid arrows)      │  (Operator)  │     │  (Operator)  │          │
│  │ - confidence_score               │                             └──────────────┘     └──────┬───────┘          │
│  │                                  │                                                         │                  │
│  │ Label: embedding_vector is the   │                                                         ▼                  │
│  │ computed feature for similarity  │                                                ┌──────────────┐            │
│  │ search                           │                                                │   Indexing   │            │
│  └──────────────────────────────────┘                                                │   & Storage  │            │
│                                                                                      │  (Operator)  │            │
│                                                                                      └──────────────┘            │
│                                                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                  Data Flow (Pipeline)                                                      │  │
│  │                                                                                                            │  │
│  │  📄 AUTOSAR PDFs ──► [PDF Parsing] ──► [Semantic Chunking] ──► [Embedding] ──► [Metadata] ──► [Indexing]   │  │
│  │       (raw)           (extract)         (split)                (vectorize)     (enrich)      (ChromaDB)    │  │
│  │                                                                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Legend for Data Preparation View

| Symbol | Element | Description |
|--------|---------|-------------|
| Rectangle with header + attributes | **Entity** | A data entity with its schema (attributes), PK in bold |
| Rectangle (in pipeline) | **Operator** | A data transformation step in the preparation pipeline |
| Solid arrow `──►` | **Data flow** | Direction of data movement between operators |
| Dashed arrow `◄╌╌╌` | **Inputs/output** | Entity provides input to or receives output from operators |
| Rectangle with folded corner | **Note** | Additional details like parameters, SQL conditions, or constraints |
| `─── Relationship ───` | **Relationship** | Association between entities |

---

## Entity: AUTOSAR Document Chunk

The primary data entity produced by the preparation pipeline.

| Attribute | Type | Description |
|-----------|------|-------------|
| **chunk_id** *(PK)* | string | Unique identifier for each chunk |
| document_name | string | Source PDF filename (e.g., `AUTOSAR_CP_SWS_CANDriver.pdf`) |
| page_number | int | Starting page number in the source PDF |
| page_end | int | Ending page number (for multi-page chunks) |
| section_heading | string | Detected AUTOSAR section heading (e.g., "7.1.2 Com_Init") |
| chunk_text | string | The actual text content of the chunk |
| chunk_index | int | Sequential position of chunk within the document |
| total_chunks | int | Total number of chunks from this document |
| requirement_ids | list[string] | Extracted AUTOSAR requirement IDs (e.g., `[SWS_Com_00432]`) |
| token_count | int | Estimated token count (characters / 4) |
| **embedding_vector** *(768-dim)* | float[] | Dense vector representation — the **computed feature** for similarity search |

---

## Raw Data Sources

| Document | Size | Pages | Content Type |
|----------|------|-------|-------------|
| AUTOSAR_CP_SWS_CANDriver.pdf | 1.4 MB | ~150 | CAN Driver BSW specification with APIs, configuration, and requirement IDs |
| AUTOSAR_CP_TPS_SystemTemplate.pdf | 27 MB | ~700 | System description template — largest document with complex structure |
| AUTOSAR_EXP_LayeredSoftwareArchitecture.pdf | 2.1 MB | ~100 | Architecture explanation with diagrams and layer descriptions |
| AUTOSAR_EXP_SecurityOverview.pdf | 297 KB | 26 | Security mechanisms overview — compact explanatory document |
| AUTOSAR_SWS_EthernetDriver.pdf | 792 KB | ~80 | Ethernet Driver specification with APIs and configuration |

**Total: ~1,050+ pages of AUTOSAR specifications**

---

## Operators (Data Preparation Pipeline)

### Operator 1: PDF Parsing

| Attribute | Value |
|-----------|-------|
| **Tool** | PyMuPDF (fitz) — high-performance PDF text extraction |
| **Input** | Raw AUTOSAR PDF files |
| **Output** | `ParsedDocument` with list of `ParsedPage` objects |

**Extraction targets:**
- **Full text:** All visible text content per page
- **Section headings:** Detected via regex pattern `^(\d+(?:\.\d+)*)\s+(.+)$` (e.g., "7.1.2 Com_Init")
- **Requirement IDs:** Detected via regex pattern `\[SWS_[A-Za-z]+_\d+\]` (e.g., "[SWS_Com_00432]")
- **Table detection:** Heuristic based on tab-separated lines (>10% of lines have ≥2 tabs)
- **Page metadata:** Page number, character count, heading list

**Code reference:** [parser.py](../app/services/ingestion/parser.py)

### Operator 2: Semantic Chunking

| Attribute | Value |
|-----------|-------|
| **Strategy** | Two-level semantic splitting |
| **Input** | `ParsedDocument` |
| **Output** | List of `Chunk` objects with text + metadata |

> **Note:** `CHUNK_SIZE = 512 tokens`, `CHUNK_OVERLAP = 50 tokens`

**Splitting strategy:**

1. **Primary split:** By AUTOSAR section headings
   - Each numbered section (e.g., "7.1.2 Com_Init") becomes a logical boundary
   - Preserves the document's inherent semantic structure

2. **Secondary split:** By token count
   - Sections exceeding `CHUNK_SIZE` (default: 512 tokens) are further split
   - Overlap of `CHUNK_OVERLAP` (default: 50 tokens) between adjacent chunks
   - Sentence boundary alignment: splits prefer to break at periods

**Why this strategy?**
- AUTOSAR documents have well-defined section numbering → natural semantic boundaries
- Section-aware chunking keeps related content together (e.g., an API function and its description)
- Overlap ensures no information is lost at chunk boundaries
- Requirement IDs ([SWS_*]) are preserved within their containing chunk

**Code reference:** [chunker.py](../app/services/ingestion/chunker.py)

### Operator 3: Embedding Generation

| Attribute | Value |
|-----------|-------|
| **Model** | `nomic-embed-text` via Ollama |
| **Input** | List of chunk text strings |
| **Output** | 768-dimensional dense vectors per chunk |

**Processing:**
- Texts are embedded in batches of 50 for efficiency
- Each embedding takes ~10ms on Apple Silicon
- Retry logic with exponential backoff (2s, 4s, 8s) for transient failures
- Total embedding time for a 200-page document: ~2-3 minutes

**Why nomic-embed-text?**
- Runs locally via Ollama (no API costs)
- Strong performance on retrieval benchmarks (MTEB)
- 768 dimensions provide good precision/speed tradeoff
- Supports up to 8192 tokens per input

**Code reference:** [embedder.py](../app/services/ingestion/embedder.py)

### Operator 4: Metadata Enrichment

| Attribute | Value |
|-----------|-------|
| **Input** | Chunks with embeddings |
| **Output** | Enriched chunks with full metadata |

Each chunk is enriched with metadata for citation generation:

| Metadata Field | Source | Purpose |
|---------------|--------|---------|
| `document_name` | Filename | Identify source document in citations |
| `page_number` | PDF page index | Link to exact page for verification |
| `page_end` | Last page of chunk | Handle multi-page chunks |
| `section` | Detected heading | Show section context in citations |
| `chunk_index` | Sequential counter | Order chunks within a document |
| `total_chunks` | Total chunk count | Context for chunk position |
| `requirement_ids` | SWS regex matches | Enable requirement-level queries |
| `token_count` | Character/4 estimate | Monitor chunk size distribution |

### Operator 5: Indexing & Storage

| Attribute | Value |
|-----------|-------|
| **Input** | Enriched chunks with embeddings and metadata |
| **Output** | Persistent vector store + metadata registry |

**Vector Store (ChromaDB):**
- **Index type:** HNSW (Hierarchical Navigable Small World) — approximate nearest neighbor
- **Distance metric:** Cosine distance
- **Persistence:** Disk-backed at `data/chroma_db/`
- **Batch upsert:** Chunks inserted in batches of 500
- **Idempotent:** Re-ingesting a document deletes old chunks first

**Metadata Store (JSON):**
- Tracks document-level metadata: name, page count, chunk count, ingestion time
- Records embedding model version and chunking parameters used
- Stored at `data/metadata/documents.json`

---

## Data Quality Considerations

| Concern | Mitigation |
|---------|------------|
| **PDF extraction errors** | PyMuPDF handles most layouts; tables may lose structure — mitigated by including raw text |
| **Chunk boundary artifacts** | 50-token overlap ensures context continuity at boundaries |
| **Duplicate content** | Jaccard similarity check (>0.7) during context assembly removes near-duplicate chunks |
| **Empty/boilerplate pages** | Pages with no text content are automatically skipped during parsing |
| **Encoding issues** | UTF-8 encoding enforced throughout the pipeline |
| **Large documents** | The 27MB System Template is chunked into manageable pieces; batch embedding prevents memory overflow |
