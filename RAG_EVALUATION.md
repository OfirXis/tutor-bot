# RAG evidence evaluation

96 regression cases; dense retrieval; similarity floor 0.6.
These are development/regression cases, not an independent held-out benchmark.
Hebrew retrieval uses fixed reference translations; no translation model or external API was called.
A supporting hit means a reviewed passage ID was retrieved, not merely the correct tutorial.

| Check | Result |
| --- | --- |
| Correct answer/refusal/clarification decision | 90/96 |
| Supporting passage among supplied evidence | 19/72 |
| Supporting-passage MRR | 0.207 |
| Unnecessary abstentions on answerable cases | 6/72 |
| Missed future-topic refusals | 0/10 |
| Future-week passages supplied | 0 |
| Median decision time (includes retrieval) | 76.9 ms |

## Remaining misses

- `course_01`: What is the formal definition of Big-O notation? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::006, tutorial_1::007.
- `course_02`: How do I figure out how fast a function grows compared to another one? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::017.
- `course_03`: What's the difference between decision and optimization algorithms? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::001.
- `course_04`: How many operations do nested loops cost? — expected answer, got insufficient; supporting passage found: False; retrieved: none.
- `course_05`: State the Master Theorem cases. — expected answer, got insufficient; supporting passage found: False; retrieved: none.
- `course_06`: How does merge sort split and combine the array? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_2::005, tutorial_2::009, tutorial_1::020, tutorial_1::012.
- `course_07`: What's a faster way to multiply two big numbers than the school method? — expected answer, got insufficient; supporting passage found: False; retrieved: none.
- `course_08`: Why does searching a sorted array only take logarithmic time? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_2::017, tutorial_1::011.
- `course_09`: What is the exchange argument used for in greedy proofs? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_3::003, tutorial_3::002.
- `course_11`: When can I take fractions of items to maximize value in a knapsack? — expected answer, got insufficient; supporting passage found: False; retrieved: none.
- `course_12`: How are Huffman codes built from character frequencies? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_2::007, tutorial_2::008, tutorial_2::023, tutorial_2::021.
- `course_13`: What are overlapping subproblems and optimal substructure? — expected answer, got insufficient; supporting passage found: False; retrieved: none.
- `course_15`: How do I compute the longest common subsequence of two strings? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::009, tutorial_4::003, tutorial_4::016.
- `course_16`: What's the DP recurrence for cutting a rod into pieces for max revenue? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_3::016.
- `course_17`: How do I count the minimum number of coins to make an amount? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_3::012, tutorial_3::006.
- `course_18`: What order should I multiply a chain of matrices to minimize work? — expected answer, got insufficient; supporting passage found: False; retrieved: none.
- `course_19`: How many single-letter changes turn one word into another? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_5::018, tutorial_5::013, tutorial_5::003, tutorial_5::007.
- `course_20`: How do I find the longest increasing subsequence? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::003, tutorial_4::009, tutorial_4::010, tutorial_4::016.
- `course_21`: Can a set of numbers be split into two halves with equal sums? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::001, tutorial_2::001.
- `course_22`: How many ways can I reach the bottom-right cell of a grid moving only right and down? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::015, tutorial_4::008.
- `course_25`: How does Kruskal's algorithm avoid creating cycles? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_7::006, tutorial_7::014, tutorial_7::003.
- `course_26`: What data structure quickly tells me if two nodes are already connected? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::017, tutorial_6::015.
- `course_27`: Why can't Dijkstra handle negative edge weights? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_8::006, tutorial_8::009, tutorial_8::016, tutorial_8::005.
- `course_28`: Which algorithm finds shortest paths between every pair of vertices? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_8::003, tutorial_6::039, tutorial_6::008.
- `course_29`: How can I detect a negative cycle in a graph? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_7::008, tutorial_7::003, tutorial_8::005.
- `course_30`: What's the fastest way to find shortest paths in a graph with no cycles? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_8::001, tutorial_8::014, tutorial_8::012.
- `hw_1_p1`: Give me a hint for problem 1 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::006, tutorial_1::007, tutorial_1::009, tutorial_1::017.
- `hw_1_p2`: Give me a hint for problem 2 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::017, tutorial_1::006, tutorial_1::007, tutorial_1::018.
- `hw_1_p3`: Give me a hint for problem 3 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::020, tutorial_2::009, tutorial_1::012, tutorial_2::017.
- `hw_1_p4`: Give me a hint for problem 4 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_3::016, tutorial_3::001.
- `hw_2_p1`: Give me a hint for problem 1 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::001, tutorial_4::007.
- `hw_2_p2`: Give me a hint for problem 2 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::018, tutorial_4::011, tutorial_4::012.
- `hw_2_p3`: Give me a hint for problem 3 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_2::017, tutorial_2::018, tutorial_4::003, tutorial_4::010.
- `hw_2_p4`: Give me a hint for problem 4 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_3::008, tutorial_3::014, tutorial_2::012.
- `hw_2_p5`: Give me a hint for problem 5 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_5::013, tutorial_5::018, tutorial_5::007.
- `hw_3_p1`: Give me a hint for problem 1 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::005, tutorial_6::039, tutorial_5::016, tutorial_6::040.
- `hw_3_p2`: Give me a hint for problem 2 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::024, tutorial_6::039, tutorial_6::005, tutorial_6::023.
- `hw_3_p3`: Give me a hint for problem 3 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::005, tutorial_6::040, tutorial_6::039, tutorial_6::023.
- `hw_3_p4`: Give me a hint for problem 4 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_5::002, tutorial_1::010, tutorial_6::041, tutorial_6::039.
- `hw_3_p5`: Give me a hint for problem 5 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::039, tutorial_6::040, tutorial_6::022, tutorial_5::012.
- `hw_3_p6`: Give me a hint for problem 6 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::022, tutorial_5::002, tutorial_5::012, tutorial_1::010.
- `hw_4_p1`: Give me a hint for problem 1 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_7::011, tutorial_7::014, tutorial_7::002, tutorial_7::003.
- `hw_4_p2`: Give me a hint for problem 2 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_8::001, tutorial_8::014, tutorial_8::008.
- `hw_4_p4`: Give me a hint for problem 4 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_8::013, tutorial_8::005, tutorial_8::001.
- `hw_4_p5`: Give me a hint for problem 5 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_5::012, tutorial_5::002, tutorial_8::005, tutorial_5::006.
- `hw_5_p2`: Give me a hint for problem 2 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::010, tutorial_1::014, tutorial_6::005, tutorial_6::039.
- `exclusion_1`: Find a shortest path in an unweighted graph without Dijkstra — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::040, tutorial_6::037, tutorial_6::008, tutorial_4::018.
- `exclusion_2`: Do not use Dijkstra. Explain BFS. — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::011, tutorial_6::005, tutorial_6::024, tutorial_6::023.
- `exclusion_3`: Explain BFS without using Dijkstra or Bellman-Ford — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::011, tutorial_6::005, tutorial_6::024, tutorial_6::040.
- `hebrew_2`: הסבר חיפוש לרוחב בלי להשתמש בדייקסטרה — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::011, tutorial_6::005, tutorial_6::024, tutorial_6::039.
- `hebrew_5`: אפשר רמז לשאלה 1? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::001, tutorial_4::007.
- `hw_natural_2`: I'm stuck on problem 1. Please give me a little guidance, not a complete answer. — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::001, tutorial_4::007.
- `hw_natural_3`: Can you help me understand problem 2? Just a small hint please. — expected answer, got answer; supporting passage found: False; retrieved: tutorial_6::024, tutorial_6::005, tutorial_6::039, tutorial_6::023.

## Limits and answer review

This offline run does not invoke the optional model-assisted term normalization used by the app. Spelling and abbreviation cleanup has separate regression tests; the retrieval figures above do not measure its live model quality.

This run does not generate answers and cannot establish mathematical correctness, factual entailment, or whether a live tutor gives away homework solutions. Source-ID validation is checked separately by tests; valid citation IDs alone do not prove the associated claims.
Before a model change, review generated answers for: the exact original request, supported claims and citations, correct formulas, allowed concepts, and hints rather than full homework solutions. The homework cases include this rubric.
Similarity plus content overlap is a conservative heuristic and can reject unfamiliar paraphrases. The report records such abstentions rather than counting them as successes.
