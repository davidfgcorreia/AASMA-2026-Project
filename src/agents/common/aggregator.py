"""Aggregator for building LLM request messages for agents.

This module composes the play context, common context, and agent-specific
context/memory/prompt into a set of messages ready to be sent to an LLM.

Usage:
    from agents.common.aggregator import build_agent_messages
    msgs = build_agent_messages('captain', scenario='default')

The returned value is a list of chat messages: [{'role': 'system', 'content': '...'}, ...]
"""
from pathlib import Path
from typing import List, Dict, Optional


AGENTS_DIR = Path(__file__).resolve().parent.parent
COMMON_DIR = Path(__file__).resolve().parent


def _read(path: Path) -> str:
    if not path or not path.exists():
        return ""
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ""


def choose_prompt_path(agent: str, scenario: Optional[str] = None) -> Optional[Path]:
    base = AGENTS_DIR / agent
    # Prefer scenario-specific prompt file: prompt_<scenario>.md
    if scenario:
        p = base / f'prompt_{scenario}.md'
        if p.exists():
            return p
    # Fallbacks
    for candidate in ('prompt.md', 'prompt.txt', 'dev_prompt.md'):
        p = base / candidate
        if p.exists():
            return p
    # Try common dev prompt
    p = COMMON_DIR / 'dev_prompt.md'
    if p.exists():
        return p
    return None


def build_agent_messages(agent: str, scenario: Optional[str] = None) -> List[Dict[str, str]]:
    """Build chat messages for the given agent.

    The composition order is:
      1. Play context
      2. Common context
      3. Agent context
      4. Agent memory
      5. Agent prompt (selected by scenario)

    Returns a list of dicts suitable for OpenAI-like chat APIs.
    """
    msgs: List[Dict[str, str]] = []

    # play context
    play_text = _read(COMMON_DIR / 'play_context.md')

    # common context
    common_ctx = _read(COMMON_DIR / 'context.md')

    # agent-specific files
    agent_dir = AGENTS_DIR / agent
    agent_ctx = _read(agent_dir / 'context.md')
    agent_mem = _read(agent_dir / 'memory.md')

    # choose prompt
    prompt_path = choose_prompt_path(agent, scenario)
    prompt_text = _read(prompt_path) if prompt_path else ''

    # Combine the user-facing content into a single user message.
    parts = []
    if play_text:
        parts.append('--- PLAY CONTEXT ---\n')
        parts.append(play_text)
    if common_ctx:
        parts.append('\n--- COMMON CONTEXT ---\n')
        parts.append(common_ctx)
    if agent_ctx:
        parts.append('\n--- AGENT CONTEXT ---\n')
        parts.append(agent_ctx)
    if agent_mem:
        parts.append('\n--- AGENT MEMORY ---\n')
        parts.append(agent_mem)
    if prompt_text:
        parts.append('\n--- PROMPT ---\n')
        parts.append(prompt_text)

    user_content = '\n'.join(parts).strip()
    if user_content:
        msgs.append({'role': 'user', 'content': user_content})

    return msgs


def build_request_payload(agent: str, scenario: Optional[str] = None) -> Dict[str, object]:
    """Return a payload dict containing messages and metadata for an LLM call."""
    messages = build_agent_messages(agent, scenario)
    return {
        'agent': agent,
        'scenario': scenario,
        'messages': messages,
        'prompt_path': str(choose_prompt_path(agent, scenario) or ''),
    }


if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Build LLM messages for an agent')
    parser.add_argument('agent', help='agent name (folder under src/agents)')
    parser.add_argument('--scenario', help='optional scenario name', default=None)
    args = parser.parse_args()

    payload = build_request_payload(args.agent, args.scenario)
    print(json.dumps(payload, indent=2))
