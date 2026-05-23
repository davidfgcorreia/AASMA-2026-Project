"""Start-position helpers for `TeamAgentManager`.

Uses the project's dev model runner to synchronously request a start
position from a configured LLM run. Falls back to a deterministic
choice when the model call fails or returns invalid coordinates.
"""

from __future__ import annotations

from captain_sonar.map_loader import MapData
from agents.common.functions import call_agent_activity_with_context
from pathlib import Path
import os
import re


def start_position(map_data: MapData):
    """Compute a start position for the team using the dev model runner.

    Returns an (x, y) tuple or None on failure.
    """
    base = Path(__file__).resolve().parent
    repo_root = base.parent.parent
    prompt_path = repo_root / "captain" / "prompts" / "0_startup.md"
    context_path = base / "map_context.md"

    # ensure output dir exists and write an early entry marker so we know function ran
    out_file = base / "startup_output.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_file.write_text("ENTRY: _start_position called\n", encoding="utf-8")
    except Exception as e:
        # If writing fails, raise so caller sees the problem
        raise

    prompt = prompt_path.read_text(encoding="utf-8")
    context = context_path.read_text(encoding="utf-8") if context_path.exists() else ""


    # Use the common call_agent_activity helper so provider keys and context are handled
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    role = "capitan"
    try:
        result = call_agent_activity_with_context(
            model=model,
            prompt=prompt,
            context=context,
            role=role,
            temperature=1,
            max_output_tokens=256,
            timeout_seconds=30.0

        )
        # result is GeminiResponse-like with `.text`
        output = getattr(result, "text", None) or getattr(result, "response_text", "")
        # record provider info if available
        provider = getattr(result, "model", None)
        with open(out_file, "a", encoding="utf-8") as fh:
            fh.write(f"provider={provider}\n")
    except Exception as exc:
        # write error to output file for inspection and raise
        out_file = base / "startup_output.md"
        err_text = f"LLM call failed: {type(exc).__name__}: {exc}\n"
        out_file.write_text(err_text, encoding="utf-8")
        raise RuntimeError("LLM start-position call failed; see startup_output.md for details") from exc

    # always persist model output for debugging (append)
    out_file = base / "startup_output.md"
    with open(out_file, 'a', encoding='utf-8') as fh:
        fh.write('\n--- MODEL OUTPUT ---\n')
        fh.write((output or '').rstrip() + "\n")

    # parse coords (strict)
    if not output:
        raise ValueError("LLM returned empty output for start position; see startup_output.md")

    s = output.strip()
    m = re.search(r"\b(\d{1,3})\s*,\s*(\d{1,3})\b", s)
    if m:
        parsed = (int(m.group(1)), int(m.group(2)))
    else:
        m = re.search(r"x\s*[:=]\s*(\d{1,3}).*?y\s*[:=]\s*(\d{1,3})", s, re.IGNORECASE)
        if m:
            parsed = (int(m.group(1)), int(m.group(2)))
        else:
            raise ValueError("Could not parse coordinates from LLM output; see startup_output.md")

    x, y = parsed
    if not map_data.in_bounds(x, y):
        raise ValueError(f"LLM returned out-of-bounds coordinates: {(x,y)}; see startup_output.md")
    if map_data.is_blocked(x, y):
        raise ValueError(f"LLM returned blocked coordinates: {(x,y)}; see startup_output.md")


    return (x, y)




