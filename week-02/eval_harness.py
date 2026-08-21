import json
import time
from classifier import classify

# Each case: (message, expected_category, expected_priority, expected_sentiment, expected_needs_human)
EVAL_SET = [
    ("I've been charged twice for my subscription this month and no one has responded to my last two emails!", "billing", "high", "negative", True),
    ("How do I reset my password?", "account", "low", "neutral", False),
    ("Your app keeps crashing every time I try to upload a file.", "technical", "high", "negative", True),
    ("Can you tell me what plans you offer?", "general", "low", "neutral", False),
    ("This is the third time I've contacted support about the same bug. I'm extremely frustrated.", "technical", "high", "negative", True),
    ("Just wanted to say thanks, your support team fixed my issue super fast!", "general", "low", "positive", False),
    ("I need to update my billing address.", "billing", "low", "neutral", False),
    ("The website is down for me, is there an outage?", "technical", "high", "neutral", False),
    ("I think I was overcharged, can someone check my invoice?", "billing", "medium", "neutral", True),
    ("My account got locked after I tried logging in from a new device.", "account", "high", "negative", True),
    ("This is unacceptable, I want a full refund immediately.", "billing", "high", "negative", True),
    ("I suspect someone accessed my account without permission.", "account", "urgent", "negative", True),
]


def run_eval(prompt_version="v1"):
    correct = {"category": 0, "priority": 0, "sentiment": 0, "needs_human": 0}
    total = len(EVAL_SET)
    rows = []

    for msg, exp_cat, exp_pri, exp_sent, exp_human in EVAL_SET:
        result, error = classify(msg)
        if error:
            print(f"FAILED: {msg[:40]}... -> {error}")
            time.sleep(5)
            continue

        cat_ok = result.category == exp_cat
        pri_ok = result.priority == exp_pri
        sent_ok = result.sentiment == exp_sent
        human_ok = result.needs_human == exp_human

        correct["category"] += cat_ok
        correct["priority"] += pri_ok
        correct["sentiment"] += sent_ok
        correct["needs_human"] += human_ok

        rows.append({
            "message": msg, "expected": (exp_cat, exp_pri, exp_sent, exp_human),
            "actual": (result.category, result.priority, result.sentiment, result.needs_human),
            "all_correct": cat_ok and pri_ok and sent_ok and human_ok
        })

        print(f"{'✓' if (cat_ok and pri_ok and sent_ok and human_ok) else '✗'} {msg[:50]}")
        time.sleep(5)  # stay under 15 req/min

    accuracy = {k: round(v / total * 100, 1) for k, v in correct.items()}
    print(f"\n--- Accuracy ({prompt_version}) ---")
    for field, pct in accuracy.items():
        print(f"{field}: {pct}%")

    return rows, accuracy


if __name__ == "__main__":
    rows, accuracy = run_eval("v1")

    with open("eval_results_v1.json", "w") as f:
        json.dump({"rows": rows, "accuracy": accuracy}, f, indent=2)
    print("\nSaved to eval_results_v1.json")