# Gemini Model Selection

This repository uses the Gemini REST API through `src/agents/common/gemini.py` and loads the API key from `src/agents/.env`.
The development harness reads its current-run settings from `src/agents/common/dev_run.json`.

Primary choices for this workspace:

- `gemini-3.1-flash-lite`: main default for everyday agent development, quick checks, and prompt iteration.
- `gemini-2.5-flash`: heavier fallback when you want more reasoning depth while keeping response times reasonable.
- `gemini-3-flash` (preview): heavier fallback for stronger model behavior when you want the newest Flash line.

Best free OpenRouter choices for this workspace:

- `deepseek/deepseek-v4-flash:free`: strong free general-purpose model for fast text work.
- `openai/gpt-oss-20b:free`: solid free open-weight model for general reasoning and development checks.
- `nvidia/nemotron-3-nano-30b-a3b:free`: good free lightweight option for agent-style tasks.
- `openrouter/free`: router that picks from free models automatically when you only need a zero-cost fallback.

Best Groq free-plan choices for this workspace:

- `llama-3.1-8b-instant`: best default for the game loop because it gives the best speed-to-budget balance for many short agent turns.
- `meta-llama/llama-4-scout-17b-16e-instruct`: better fallback when a turn needs stronger reasoning or broader context.
- `qwen/qwen3-32b`: useful when you want a stronger non-llama option and can afford the lower throughput.
- `groq/compound-mini`: use only if you want Groq's agentic routing and can keep prompts compact.
- `groq/compound`: reserve for experiments; the token budget is too tight for a busy game loop.

Selection guidance:

- Use `gemini-3.1-flash-lite` for the normal loop unless a task clearly needs more depth.
- Use `gemini-2.5-flash` when the lighter model is not enough for debugging or multi-step reasoning.
- Use `gemini-3-flash` when you want to test the latest Flash behavior and accept preview-model instability.
- Use the OpenRouter free models when you want zero-cost experiments, but expect availability and behavior to change more often.
- Use `llama-3.1-8b-instant` on Groq for the main agent loop, and only move up to larger or more specialized Groq models when a turn is clearly failing on reasoning quality.
- Avoid building the core game loop around `groq/compound` or `groq/compound-mini` unless you have already confirmed the prompt size stays very small.
- Do not plan around models outside the primary Gemini set unless access changes later.

Source:

- Google Gemini model documentation: https://ai.google.dev/gemini-api/docs/models/gemini