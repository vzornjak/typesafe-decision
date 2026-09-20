# Blind evaluation rubric

Evaluators do not see arm IDs, repetition IDs, selection traces, model usage, latency, or cost.

For each randomized answer:

1. **Requirement completion (0–2 per requirement)**
   - 0: absent or materially wrong;
   - 1: partially addressed or important limitation omitted;
   - 2: adequately addressed from supplied evidence.
2. **Citation correctness**
   - label each material cited claim as supported, partially supported, unsupported, contradicted, wrong source, or insufficient evidence;
   - verify the cited candidate ID and gold support span.
3. **Contradictions/errors**
   - count material claims contradicted by gold sources or by the cited source.
4. **Overall usefulness (1–5)**
   - 1 unusable, 2 major deficiencies, 3 adequate with notable gaps, 4 strong, 5 excellent;
   - judge correctness, coverage, clarity, and appropriate uncertainty together.
5. **Review notes**
   - quote the answer span responsible for every score below full credit.

The primary quality score is overall usefulness. The preregistered noninferiority margin is 0.25 points on the 1–5 scale. Evaluators must not compare answers side by side while labeling; paired analysis happens afterward.
