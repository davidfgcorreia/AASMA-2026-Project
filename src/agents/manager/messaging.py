"""Messaging helpers for `TeamAgentManager`.

This module centralizes the bounded inter-agent messaging logic so the
manager implementation can remain focused on orchestration. Functions
operate on a `TeamAgentManager` instance passed as `manager` and manipulate
its internal inbox and pair-count bookkeeping.
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from ..base import AgentRole
from .models import AgentMessage


def send_message(manager, sender: AgentRole, recipient: AgentRole | None, text: str, metadata: dict[str, Any] | None = None) -> bool:
    if sender not in manager._agents:
        return False
    if len(text) > manager.config.max_message_length:
        return False
    if len(manager._messages_this_turn) >= manager.config.max_messages_per_turn:
        return False

    message = AgentMessage(
        sender=sender,
        recipient=recipient,
        turn_id=manager._turn_id,
        text=text,
        metadata=dict(metadata or {}),
    )

    if recipient is None:
        recipients = [role for role in manager._active_roles if role != sender]
    else:
        recipients = [recipient] if recipient in manager._agents else []

    delivered = False
    for role in recipients:
        pair_key = (sender, role)
        if manager._pair_counts.get(pair_key, 0) >= manager.config.max_messages_per_pair_per_turn:
            continue
        manager._pair_counts[pair_key] = manager._pair_counts.get(pair_key, 0) + 1
        manager._inbox[role].append(message)
        delivered = True

    if delivered:
        manager._messages_this_turn.append(message)
    return delivered


def broadcast(manager, sender: AgentRole, text: str, metadata: dict[str, Any] | None = None) -> bool:
    return send_message(manager, sender, None, text, metadata)


def read_inbox(manager, role: AgentRole) -> list[dict[str, Any]]:
    return [serialize_message(manager, message) for message in manager._inbox.get(role, [])]


def serialize_message(manager, message: AgentMessage) -> dict[str, Any]:
    return {
        "sender": message.sender.value,
        "recipient": message.recipient.value if message.recipient is not None else None,
        "turn_id": message.turn_id,
        "text": message.text,
        "metadata": dict(message.metadata),
    }
