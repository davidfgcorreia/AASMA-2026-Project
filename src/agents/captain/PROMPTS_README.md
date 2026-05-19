# Captain Decision-Making Pipeline

This document explains the three-phase decision-making architecture for the Captain agent.

## Overview

The Captain decision-making process is split into **three distinct phases**, each with its own prompt and focus:

1. **Phase 1: Analysis** - Individual model reasoning on game state and strategy
2. **Phase 2: Discussion** - Multi-agent consensus building
3. **Phase 3: Action** - Final action formulation with exact parameters

Each phase builds on the previous one, creating a structured approach to tactical decision-making.

## File Structure

```
src/agents/captain/
├── prompts/
│   ├── 1_analysis.md      # Phase 1: State analysis and strategic reasoning
│   ├── 2_discussion.md    # Phase 2: Collaborative discussion and consensus
│   └── 3_action.md        # Phase 3: Final action formulation
├── strategy.md             # Strategic guide and decision framework (context injection)
├── action_format.md        # Action format reference (context injection)
├── context.md              # Agent role context
├── memory.md               # Agent memory
└── prompt.md               # Original single-prompt version (deprecated)
```

## How to Use These Files

### Basic Workflow

**Step 1: Phase 1 - Individual Analysis**
- Use prompt from `prompts/1_analysis.md`
- Provide: game state, memory, context, strategy guide
- Output: Individual model's direction/system recommendation with reasoning

**Step 2: Phase 2 - Group Discussion**
- Use prompt from `prompts/2_discussion.md`
- Provide: All Phase 1 outputs, original context, strategy guide
- Output: Team consensus on direction and system to use

**Step 3: Phase 3 - Action Formulation**
- Use prompt from `prompts/3_action.md`
- Provide: Phase 2 consensus decision, current game state, action format reference
- Output: Complete action in proper format ready for execution

### Context Injection

When building agent messages for any phase, inject these context files:

1. **Always include:**
   - `strategy.md` - Strategic framework for all decisions
   - `action_format.md` - For Phase 3, reference for proper formatting

2. **Include based on phase:**
   - Phase 1: Game state, memory, context, strategy guide
   - Phase 2: Phase 1 outputs, original inputs, strategy guide
   - Phase 3: Phase 2 consensus, current game state, action format reference

## Example Usage

### Updating the Aggregator

To integrate these prompts into the aggregator:

```python
# Choose prompt based on phase parameter
def choose_prompt_path(agent: str, scenario: Optional[str] = None, phase: Optional[int] = None) -> Optional[Path]:
    base = AGENTS_DIR / agent
    
    # If phase is specified, use phase-specific prompt
    if phase and 1 <= phase <= 3:
        p = base / 'prompts' / f'{phase}_*.md'
        if p.exists():
            return p
    
    # Otherwise use scenario-specific or default
    if scenario:
        p = base / f'prompt_{scenario}.md'
        if p.exists():
            return p
    
    # Fallback to default prompt
    for candidate in ('prompt.md', 'prompt.txt'):
        p = base / candidate
        if p.exists():
            return p
    
    return None
```

### Injecting Strategy and Action Format

```python
def build_agent_messages(agent: str, phase: Optional[int] = None, scenario: Optional[str] = None):
    msgs = []
    
    # System instruction (if still used)
    # ... existing code ...
    
    # Play context
    play_text = _read(COMMON_DIR / 'play_context.md')
    
    # Agent context
    agent_ctx = _read(AGENTS_DIR / agent / 'context.md')
    
    # Strategy guide (always for captain)
    if agent == 'captain':
        strategy_text = _read(AGENTS_DIR / agent / 'strategy.md')
    
    # Action format reference (for captain phase 3)
    if agent == 'captain' and phase == 3:
        action_fmt = _read(AGENTS_DIR / agent / 'action_format.md')
    
    # ... rest of aggregation ...
```

## Decision Quality

The three-phase approach improves decision quality by:

1. **Diversity**: Phase 1 allows multiple models to analyze independently
2. **Reasoning**: Each phase requires explicit justification
3. **Consensus**: Phase 2 forces debate and alignment on strategy
4. **Precision**: Phase 3 ensures exact format and validation
5. **Traceability**: Clear link from strategy → consensus → action

## When to Use Single-Phase

For simpler scenarios or real-time constraints:
- Use `prompt.md` (deprecated) for a single prompt covering all logic
- Or integrate all phases into a single more complex prompt

For learning and debugging:
- Use Phase 1 to understand individual model reasoning
- Use Phase 2 to see where models disagree
- Use Phase 3 to verify action correctness

## Adding New Phases

To add additional decision phases (e.g., post-action review):

1. Create new file: `prompts/4_review.md`
2. Define inputs (outputs from Phase 3)
3. Define outputs (learning/memory updates)
4. Update this README
5. Integrate into aggregator logic

## Files Reference

| File | Purpose | Used In |
|------|---------|---------|
| `strategy.md` | Strategic priorities and decision framework | All phases, context injection |
| `action_format.md` | Complete action specification and examples | Phase 3, validation |
| `1_analysis.md` | Individual reasoning prompt | Phase 1 execution |
| `2_discussion.md` | Consensus-building prompt | Phase 2 execution |
| `3_action.md` | Final action formulation | Phase 3 execution |
| `context.md` | Captain role definition | All phases |
| `memory.md` | Captain's game memory | Phase 1, 2 |
