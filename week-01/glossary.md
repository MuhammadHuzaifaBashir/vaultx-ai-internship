Token — a chunk of text (often a word-piece, sometimes a whole word or just punctuation) that the model reads and generates one unit at a time. "internship" might be one token or split into two.

Context window — the maximum number of tokens (input + output combined) the model can "see" at once in a single request. Gemini 2.5 Flash has a very large window (around 1M tokens), but every request still gets billed and limited by it.

Temperature — a number that controls randomness in the next-token choice. Low temperature (0) = deterministic, picks the most likely token every time. High temperature (close to 1–2 on Gemini) = more varied, creative, sometimes less coherent output.

Top-p (nucleus sampling) — instead of picking from all possible next tokens, the model only samples from the smallest set of tokens whose combined probability adds up to p. Lower top-p = narrower, safer choices.

System prompt / system instruction — an instruction given to the model before the conversation starts that sets its role, tone, or constraints, separate from the user's actual message. In Gemini this is the system_instruction field.

Embedding — a numeric vector representation of text (or other data) that captures its meaning, so that texts with similar meaning end up as vectors that are close together. Used for search, clustering, and retrieval.

Hallucination — when a model generates text that sounds plausible and confident but is factually wrong or made up, because it's predicting likely-sounding text, not looking facts up.

Fine-tuning — taking a pretrained model and continuing to train it on a smaller, task-specific dataset so it adapts its behavior/style/knowledge to that task.

Inference — the act of running a trained model on new input to get an output (as opposed to training, where the model's weights are being updated).

Base vs instruction-tuned model: a base model is trained purely to predict the next token from raw text and will often just continue your prompt rather than "answer" it. An instruction-tuned model has been further trained (via supervised fine-tuning + RLHF-style methods) specifically to follow instructions and hold a conversation, which is why chatting with gemini-2.5-flash feels like talking to an assistant rather than autocomplete.

Why an LLM predicts text rather than "knows" facts (write ~3 sentences in your own words): the core mechanism is next-token prediction learned from statistical patterns in training text — the model has no built-in fact database or way to check truth. It only produces the sequence of tokens that its training makes most statistically likely to follow the prompt. That's why it can state wrong things fluently and confidently — it's optimizing for plausible continuation, not verified accuracy.
