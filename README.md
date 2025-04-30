PDF → MinerU

→ content list JSON (main input for LLM & graph generation)
→ middle.json (UI highlights + span anchors)
→ MD output (optional for exports)

↓
LLM Summarizer + Entity/Relation Extractor
↓
Graphiti JSON: nodes + edges with source anchoring
↓
Zep: Embed sections + paragraphs + sentences
↓
Frontend (Next.js + react-pdf + Graphiti):
  - Hover text = highlight in PDF
  - Click on node = scroll to paragraph
  - Summary view per section = toggleable