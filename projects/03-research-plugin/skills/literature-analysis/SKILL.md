---
name: literature-analysis
description: Analyze research papers using evidence-first retrieval and source-grounded synthesis.
---

# Literature Analysis

When the task depends on the paper corpus:

1. Clarify the research question if the requested comparison target is ambiguous.
2. Use the research retrieval tool before making factual claims about papers.
3. Preserve `doc_id`, `page`, and `chunk_id` from tool results.
4. Distinguish a paper in the local corpus from a paper merely mentioned in references.
5. If the retrieved evidence is insufficient, say so instead of filling the gap from memory.
6. For cross-paper questions, gather evidence from more than one relevant corpus document before synthesizing.
7. Keep quotations short; prefer paraphrase plus source provenance.
