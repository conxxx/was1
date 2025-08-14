# Appendix D: Evaluation artifacts (internal)

Purpose: Document how the internal evaluations were run and where artifacts live.

## D.1 Needle-in-a-Haystack (10/10)
- Corpus: combined_haystack.txt (repository root). ~150 pages with a single hidden "needle" sentence embedded.
- Method: Ask direct and paraphrased queries targeting the needle; verify retrieval and grounded answer.
- Result: 10/10 retrieval and correct grounding.

## D.2 Specialized 50-QA set (≈96%)
- Source: curated domain questions (internal doc with maintainers).
- Grading: LLM-as-judge using Gemini 2.5 Pro with semantic similarity rubric.
- Result: ≈96% accuracy.

Notes
- Keep these artifacts internal; update this appendix if file paths or grading configs change.
