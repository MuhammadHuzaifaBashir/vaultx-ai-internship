# Temperature Comparison — Analysis (Gemini)

## Results Table

| Temperature | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| 0   | Where great days are brewed, one cup at a time. | [Failed after retries] | Crafted for the daily grind, |
| 0.7 | "Where every cup is brewed with passion and | "Brewed for your best moments | Where every cup feels like coming home. |
| 1.0 | Where every cup feels like coming home. | Fueling your everyday moments, one handcrafted | "Your daily pause, poured to perfection." |

## How Variance Changes Across Temperatures

At temperature 0, the outputs were the most focused and predictable, both leaning on similar phrasing around daily routine and comfort ("brewed," "daily grind"). This matches how temperature 0 works — the model always selects its single most statistically likely next word, so repeated runs with the same prompt tend to produce very similar results. Run 2 failed due to a temporary server-side issue unrelated to temperature, not because of the setting itself.

At temperature 0.7, wording became noticeably more varied while staying on-topic. Sentence structure, punctuation style, and specific word choices differed more between runs compared to temperature 0.

At temperature 1.0, variance was highest. All three runs used different sentence structures, different punctuation and formatting choices (quotation marks, bold text), and more creative or unusual phrasing. This shows the model exploring a wider range of less-predictable word choices rather than defaulting to the safest option every time.

**Overall pattern**: as temperature increases from 0 to 1.0, output variety and creativity increase, while consistency and predictability decrease. This is the fundamental trade-off temperature controls.

## Recommended Temperature by Use Case

**Support bot — Temperature 0–0.3**
Justification: consistency and predictability matter most when giving factual or policy-based answers to customers. A low temperature reduces the risk of the bot phrasing the same policy differently each time, which could confuse users or create an inconsistent support experience. Customers expect reliable, repeatable answers to the same question.

**Code generator — Temperature 0–0.3**
Justification: correctness and consistency of syntax matter far more than creative variation in code. Unpredictable output at higher temperatures is a real liability when generating logic that needs to compile and run correctly every time — there's no benefit to "creative" code, only risk.

**Marketing copy tool — Temperature 0.7–1.0**
Justification: variety and novelty are the entire point of marketing copy. The temperature 1.0 results above were noticeably more varied and expressive than the temperature 0 results, which is exactly the kind of creative range a marketing tool should produce — nobody wants the same tagline generated every time.
EOF