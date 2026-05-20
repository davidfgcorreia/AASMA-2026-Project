#!/usr/bin/env python3
"""First Mate entrypoint: build the first-mate context and run the shared dev LLM harness.

This script assembles the first-mate prompt payload used by the shared development
runner, then invokes `agents.common.dev_main` with the first-mate config so the
LLM runs with the prompt and files already wired in the repository.
"""
from pathlib import Path
import argparse
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description='Build LLM payload for first mate agent')
    parser.add_argument('--scenario', '-s', help='Optional scenario name to select a prompt', default=None)
    parser.add_argument('--out', '-o', help='Write the generated first-mate context file (optional). If a bare filename is provided it will be placed in the first-mate folder.')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON')
    parser.add_argument('--build-only', action='store_true', help='Only build the first-mate payload file and skip the shared dev runner')
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[3]
    agent_dir = Path(__file__).resolve().parent
    context_path = agent_dir / 'context.md'
    memory_path = agent_dir / 'memory.md'
    strategy_path = agent_dir / 'strategy.md'
    play_path = agent_dir.parent / 'common' / 'play_context.md'

    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding='utf-8')
        except Exception:
            return ''

    strategy_text = _read(strategy_path).rstrip()
    memory_text = _read(memory_path).rstrip()
    context_text = _read(context_path).rstrip()
    play_text = _read(play_path).rstrip()

    # Place each file one after the other in the requested order
    parts = []
    if strategy_text:
        parts.append(strategy_text)
    if memory_text:
        parts.append(memory_text)
    if context_text:
        parts.append(context_text)
    if play_text:
        parts.append(play_text)
    md_content = "\n\n".join(parts).strip() + "\n"

    if args.out:
        out_path = Path(args.out)
        if out_path.parent == Path('.') or out_path.parent == Path(''):
            out_path = agent_dir / out_path.name
        if out_path.suffix.lower() != '.md':
            out_path = out_path.with_suffix('.md')
    else:
        out_path = agent_dir / 'first_mate_payload.md'

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md_content, encoding='utf-8')
    print(f'Wrote Markdown payload to {out_path}', file=sys.stderr)

    if args.build_only:
        return

    # Prefer an agent-specific dev run config if present, otherwise use the common one.
    agent_dev_config = agent_dir / 'dev_run.json'
    common_dev_config = repo_root / 'src' / 'agents' / 'common' / 'dev_run.json'
    dev_config = agent_dev_config if agent_dev_config.exists() else common_dev_config
    subprocess.run(
        [sys.executable, '-m', 'agents.common.dev_main', '--config', str(dev_config)],
        check=True,
    )


if __name__ == '__main__':
    main()