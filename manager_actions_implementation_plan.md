# Manager Actions Implementation Plan

## Goal
Build the action pipeline from agent discussion to validated game-loop execution.

This plan focuses on the manager actions path only:
- collect the right context
- run agent discussion
- choose a final captain action
- validate and parse the action
- send it into the game loop

## Scope
- Manager-side context assembly
- Agent-to-agent communication
- Shared memory updates
- Prompt-driven discussion flow
- Captain decision selection
- Action parsing and validation
- Game loop handoff

## Step 1 - Check What Is Already Implemented
Review the current codebase and identify:
- existing manager context builders
- current prompt files per agent
- current shared memory files
- current agent communication channels
- current action parsing and validation logic
- current game-loop action intake points

Deliverable:
- short implementation audit with file references
- list of missing pieces and overlap with existing code

## Step 2 - Generate Aggregated Context Files For Agent Prompts
Create the context package used by agents during a turn.

Include:
- merged memory files
- per-role context
- shared turn context
- selected prompt files
- any map, state, or team summaries needed by the role

Deliverable:
- one aggregated context bundle per turn
- consistent file format for prompt loading

## Step 3 - Review Communication Channels And Shared Memory
Inspect and define how agents communicate:
- agent-to-agent messages
- manager-mediated shared memory writes
- per-role inbox/outbox flow
- what is persistent vs turn-only

Deliverable:
- communication contract for each channel
- list of shared memory fields and update rules

## Step 4 - Run The Initial Prompt Format For The Agents
Define the first pass prompt input for each agent.

Include:
- role-specific prompt
- shared turn context
- team strategy notes
- map and belief context where needed

Deliverable:
- initial prompt assembly logic
- prompt input schema per role

## Step 5 - Discussion Phase For The Agents
Run the bounded discussion pass before final action selection.

Include:
- message exchange between roles
- refinement based on turn context
- turn-limited discussion rounds
- shared memory updates after each discussion pass

Deliverable:
- discussion loop specification
- message limits and stop conditions

## Step 6 - Captain Chooses The Full Action According To The Discussion
After discussion, the captain produces the final action package.

Include:
- captain decision synthesis
- merge of advice from other roles
- selected move/system intent
- final action structure to submit to the manager

Deliverable:
- captain final-decision step
- final action intent schema

## Step 7 - Action Is Parsed, Validated, And Sent To The Game Loop
Take the final action and pass it into execution.

Include:
- strict parsing of the returned action
- validation against allowed action types and game state
- conversion into the game-loop format
- safe handoff to the game loop

Deliverable:
- action validation layer
- game-loop execution handoff
- error handling for invalid or incomplete action outputs

## Suggested Execution Order
1. Audit what already exists.
2. Define the aggregated context format.
3. Define communication and shared-memory rules.
4. Wire the prompt assembly flow.
5. Implement the discussion loop.
6. Implement captain action selection.
7. Implement parsing, validation, and game-loop handoff.

## Notes
- Keep the action pipeline deterministic where possible.
- Treat agent output as untrusted until parsed and validated.
- Prefer a single shared context format to avoid duplicated prompt logic.

## Acceptance Checklist
- [ ] Current action-related code is audited.
- [ ] Aggregated context files are defined.
- [ ] Agent communication and shared memory rules are documented.
- [ ] Initial prompts are assembled from the correct turn context.
- [ ] Discussion phase is bounded and repeatable.
- [ ] Captain final action selection is defined.
- [ ] Final action parsing and validation feed the game loop safely.
