"""
Step 4: Evaluate the RAG system honestly.

Runs a fixed set of QA pairs against the system, checks:
  - Did it retrieve/answer from the correct source document?
  - Did a human-reviewable "correct" flag get set? (You fill this in --
    see the CSV/PDF output and mark pass/fail after reading each answer.
    This script automates the grounding check; correctness of content
    still needs a human pass, which is normal for RAG evals.)
  - Did it correctly refuse the deliberately unanswerable questions?

Outputs eval_results.json and prints a summary you can paste into your
PDF report.

NOTE: a short delay is added between each question. The free tier of
gemini-3.5-flash-lite allows 15 requests/minute; without spacing calls
out, a run of 18 questions can hit that limit partway through and fail
silently on the remaining items. 5 seconds/question keeps this run
safely under that limit (18 questions * ~5s = ~90s total).
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

rag_query = import_module("03_rag_query")

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "index")
DELAY_SECONDS = 5  # stay under the 15 requests/minute free-tier limit

# 15 answerable questions (spread across all 5 source docs) + 3
# deliberately unanswerable questions to test refusal behavior.
QA_PAIRS = [
    {"q": "How many days of annual leave do full-time employees accrue per year?",
     "expected_source": "hr_leave_policy.txt", "expected_answer_contains": "18"},
    {"q": "How many consecutive sick days trigger a requirement for a medical certificate?",
     "expected_source": "hr_leave_policy.txt", "expected_answer_contains": "2"},
    {"q": "How many weeks of paid parental leave does a primary caregiver get?",
     "expected_source": "hr_leave_policy.txt", "expected_answer_contains": "16"},
    {"q": "How long must employee passwords be?",
     "expected_source": "it_security_policy.txt", "expected_answer_contains": "14"},
    {"q": "Within how many hours must a suspected security incident be reported?",
     "expected_source": "it_security_policy.txt", "expected_answer_contains": "1"},
    {"q": "What form is required before using a third-party automation tool like n8n or Make on company systems?",
     "expected_source": "it_security_policy.txt", "expected_answer_contains": "Tool Request Form"},
    {"q": "How many business days before a new hire's start date does IT ship the laptop?",
     "expected_source": "onboarding_guide.txt", "expected_answer_contains": "2"},
    {"q": "How long is the probation period for new hires?",
     "expected_source": "onboarding_guide.txt", "expected_answer_contains": "90"},
    {"q": "How long does the onboarding buddy program last?",
     "expected_source": "onboarding_guide.txt", "expected_answer_contains": "60"},
    {"q": "What is the daily meal reimbursement cap while traveling?",
     "expected_source": "expense_policy.txt", "expected_answer_contains": "75"},
    {"q": "Within how many days of an expense being incurred must it be submitted?",
     "expected_source": "expense_policy.txt", "expected_answer_contains": "30"},
    {"q": "What expense amount requires VP-level approval?",
     "expected_source": "expense_policy.txt", "expected_answer_contains": "2,000"},
    {"q": "How many days per week are employees expected in the office under the hybrid model?",
     "expected_source": "remote_work_policy.txt", "expected_answer_contains": "2"},
    {"q": "What is the one-time home office setup stipend amount?",
     "expected_source": "remote_work_policy.txt", "expected_answer_contains": "500"},
    {"q": "How many business days per year can an employee work from abroad without special approval?",
     "expected_source": "remote_work_policy.txt", "expected_answer_contains": "20"},
    # Deliberately unanswerable -- not in any document
    {"q": "What is the company's policy on stock option vesting schedules?",
     "expected_source": None, "expected_answer_contains": "NOT_FOUND"},
    {"q": "What is the CEO's name?",
     "expected_source": None, "expected_answer_contains": "NOT_FOUND"},
    {"q": "Does NimbusWorks offer a gym membership discount?",
     "expected_source": None, "expected_answer_contains": "NOT_FOUND"},
]


def main():
    results = []
    correct_source = 0
    correct_refusal = 0
    total_answerable = sum(1 for p in QA_PAIRS if p["expected_source"])
    total_unanswerable = len(QA_PAIRS) - total_answerable

    for i, pair in enumerate(QA_PAIRS, 1):
        try:
            result = rag_query.answer_question(pair["q"])
        except Exception as e:
            print(f"Q{i}: FAILED -> {e}")
            results.append({
                "question": pair["q"],
                "expected_source": pair["expected_source"],
                "retrieved_sources": [],
                "source_match": None,
                "correctly_refused": None,
                "answer": f"ERROR: {e}",
            })
            time.sleep(DELAY_SECONDS)
            continue

        sources = [s["source"] for s in result["sources"]]

        source_hit = (
            pair["expected_source"] in sources if pair["expected_source"] else None
        )
        refused_correctly = (
            "NOT_FOUND" in result["answer"] if pair["expected_source"] is None else None
        )

        if source_hit:
            correct_source += 1
        if refused_correctly:
            correct_refusal += 1

        results.append({
            "question": pair["q"],
            "expected_source": pair["expected_source"],
            "retrieved_sources": sources,
            "source_match": source_hit,
            "correctly_refused": refused_correctly,
            "answer": result["answer"],
        })
        print(f"Q{i}/{len(QA_PAIRS)}: {pair['q']}")
        print(f"   -> {result['answer'][:150]}")
        print(f"   sources: {sources}\n")

        time.sleep(DELAY_SECONDS)  # avoid free-tier rate limit before the next call

    summary = {
        "total_questions": len(QA_PAIRS),
        "answerable_questions": total_answerable,
        "correct_source_retrieval": f"{correct_source}/{total_answerable}",
        "unanswerable_questions": total_unanswerable,
        "correctly_refused": f"{correct_refusal}/{total_unanswerable}",
    }

    out_path = os.path.join(INDEX_DIR, "eval_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    print("=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nFull results saved to {out_path}")
    print("\nNOTE: source_match measures retrieval, not answer correctness.")
    print("Read through 'answer' for each question and manually mark true/false")
    print("correctness in your PDF report -- that human check is expected as")
    print("part of an honest RAG evaluation.")


if __name__ == "__main__":
    main()
