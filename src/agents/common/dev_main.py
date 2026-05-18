from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .dev_providers import call_dev_model
from .gemini import load_env_file


DEFAULT_CONFIG_PATH = Path(__file__).with_name("dev_run.json")
DEFAULT_BASE_PATH = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Development harness for Gemini agent prompts")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="JSON file describing the current run configuration",
    )
    parser.add_argument("--prompt", help="override the prompt from the config file")
    return parser.parse_args()


def load_run_config(config_path: str | os.PathLike[str]) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Run config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Run config must be a JSON object")
    return data


def read_text_file(path_value: str | os.PathLike[str] | None, *, base_path: Path = DEFAULT_BASE_PATH) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = base_path / path
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def write_test_output(path_value: str | os.PathLike[str], content: str, *, base_path: Path = DEFAULT_BASE_PATH) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = base_path / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    load_env_file()
    args = parse_args()
    config = load_run_config(args.config)
    config_base_path = Path(args.config).resolve().parent
    prompt = args.prompt if args.prompt is not None else read_text_file(config.get("prompt_file") or config.get("prompt"))
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Set a non-empty prompt file in the run config or pass --prompt")

    context = read_text_file(config.get("context_file") or config.get("context"), base_path=config_base_path)
    system_instruction = read_text_file(
        config.get("system_instruction_file") or config.get("system_instruction"),
        base_path=config_base_path,
    )
    model = config.get("model") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    provider = ""
    response_text = ""
    error_text = None
    fallback_note = ""

    try:
        result = call_dev_model(
            model=model,
            prompt=prompt,
            context=context or None,
            system_instruction=system_instruction or None,
            temperature=config.get("temperature"),
            max_output_tokens=config.get("max_output_tokens"),
            top_p=config.get("top_p"),
            top_k=config.get("top_k"),
            timeout_seconds=config.get("timeout_seconds", 60.0),
            fallback_model=config.get("fallback_model") or os.getenv("GEMINI_FALLBACK_MODEL"),
        )
        provider = result.provider
        response_text = result.response_text
        fallback_note = result.fallback_note
        fallback_note = result.fallback_note
    except Exception as exc:  # pragma: no cover - keeps failure details in the output file
        error_text = f"{type(exc).__name__}: {exc}"
    finally:
        output_file = config.get("output_file") or "dev_output.md"
        output_lines = [
            "# Gemini Dev Run Output",
            "",
            f"- model: {model}",
            f"- provider: {provider}",
            f"- prompt_file: {config.get('prompt_file') or config.get('prompt') or ''}",
            f"- context_file: {config.get('context_file') or config.get('context') or ''}",
            f"- system_instruction_file: {config.get('system_instruction_file') or config.get('system_instruction') or ''}",
            "",
            "## Prompt",
            "",
            prompt,
            "",
            "## Context",
            "",
            context,
            "",
            "## System Instruction",
            "",
            system_instruction,
            "",
            "## Response",
            "",
            response_text,
        ]
        if error_text is not None:
            output_lines.extend(["", "## Error", "", error_text])
        if fallback_note:
            output_lines.extend(["", "## Fallback", "", fallback_note])
        write_test_output(output_file, "\n".join(output_lines), base_path=config_base_path)


if __name__ == "__main__":
    main()