"""
prompt_templates.py — VaultX Week 02, Task 01

A reusable library of prompt template functions covering the 5 core patterns:
zero-shot, few-shot, role/system, chain-of-thought, constrained output.

Each function returns a dict shaped like:
    {"system_instruction": str or None, "contents": str}
so it can be plugged straight into gemini_wrapper.GeminiWrapper.send_message().
"""


def zero_shot(task: str, input_text: str) -> dict:
    """Direct instruction, no examples, no persona."""
    return {
        "system_instruction": None,
        "contents": f"{task}\n\nInput: {input_text}",
    }


def few_shot(task: str, examples: list[tuple[str, str]], input_text: str) -> dict:
    """
    examples: list of (input, output) pairs the model learns the pattern from.
    """
    example_block = "\n\n".join(
        f"Input: {ex_in}\nOutput: {ex_out}" for ex_in, ex_out in examples
    )
    prompt = f"{task}\n\nExamples:\n{example_block}\n\nNow do the same for:\nInput: {input_text}\nOutput:"
    return {
        "system_instruction": None,
        "contents": prompt,
    }


def role_system(role_description: str, task: str, input_text: str) -> dict:
    """Sets a persona/constraint as a system instruction, separate from the user task."""
    return {
        "system_instruction": role_description,
        "contents": f"{task}\n\nInput: {input_text}",
    }


def chain_of_thought(task: str, input_text: str) -> dict:
    """Asks the model to reason step-by-step before giving a final answer."""
    prompt = (
        f"{task}\n\nInput: {input_text}\n\n"
        "Think through this step-by-step first, then on a new final line write:\n"
        "FINAL ANSWER: <your answer>"
    )
    return {
        "system_instruction": None,
        "contents": prompt,
    }


def constrained_output(task: str, input_text: str, allowed_values: list[str]) -> dict:
    """Restricts the model to a fixed, explicit set of possible outputs."""
    values_str = ", ".join(allowed_values)
    prompt = (
        f"{task}\n\nInput: {input_text}\n\n"
        f"Respond with EXACTLY one of the following values, nothing else: {values_str}"
    )
    return {
        "system_instruction": None,
        "contents": prompt,
    }


if __name__ == "__main__":
    # Quick manual test of each template (prints the constructed prompt, doesn't call the API)
    print("--- zero_shot ---")
    print(zero_shot("Classify the sentiment.", "I love this product!"))

    print("\n--- few_shot ---")
    examples = [
        ("This is amazing!", "Positive"),
        ("Worst purchase ever.", "Negative"),
    ]
    print(few_shot("Classify the sentiment.", examples, "It's okay, nothing special."))

    print("\n--- role_system ---")
    print(role_system(
        "You are a strict JSON API. Only output valid JSON, nothing else — no markdown, no explanation.",
        "Classify the sentiment.",
        "I love this product!"
    ))

    print("\n--- chain_of_thought ---")
    print(chain_of_thought("Solve this word problem.", "If a train travels 60 miles in 1.5 hours, what is its speed?"))

    print("\n--- constrained_output ---")
    print(constrained_output("Classify the sentiment.", "I love this product!", ["Positive", "Negative", "Neutral"]))
