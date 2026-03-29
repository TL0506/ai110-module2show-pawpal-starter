# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond the basic daily plan, the scheduler includes four algorithmic features:

| Feature | Method | What it does |
|---|---|---|
| **Sort by time** | `Scheduler.sort_by_time()` | Returns scheduled tasks in chronological order using a `lambda` key with `datetime.strptime` on `HH:MM` strings |
| **Filter tasks** | `Scheduler.filter_tasks(completed, pet_name)` | Filters all `(Pet, Task)` pairs by completion status and/or pet name |
| **Recurring tasks** | `Scheduler.mark_task_complete()` + `_spawn_next_occurrence()` | When a `daily` or `weekly` task is marked done, a new instance is automatically added with a `due_date` calculated using Python's `timedelta` (daily → +1 day, weekly → +7 days) |
| **Conflict detection** | `Scheduler.detect_conflicts()` | Checks every pair of scheduled tasks for overlapping windows using the interval overlap test (`a.start < b.end AND b.start < a.end`); returns human-readable warning strings instead of crashing |

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| # | Test | What it verifies |
|---|---|---|
| 1 | Task completion | `complete()` flips `is_completed` to `True` |
| 2 | Task addition | `add_task()` grows the pet's task list by exactly one |
| 3 | Sort by time | `sort_by_time()` reorders tasks from earliest to latest start time |
| 4 | Sort — empty schedule | `sort_by_time()` returns `[]` gracefully when nothing is scheduled |
| 5 | Daily recurrence | Marking a `DAILY` task done spawns a new task due the next day (`+1` via `timedelta`) |
| 6 | Weekly recurrence | Marking a `WEEKLY` task done spawns a new task due 7 days later |
| 7 | No recurrence | `AS_NEEDED` tasks do not auto-spawn a follow-up |
| 8 | Conflict detection | Overlapping time windows produce a `"CONFLICT"` warning string |
| 9 | No false conflicts | Back-to-back (adjacent) slots are **not** flagged as conflicts |
| 10 | No slots available | All tasks land in `unscheduled_tasks` when the owner has no free time |
| 11 | Task too long | A task that exceeds every slot's duration goes to `unscheduled_tasks` |
| 12 | Priority ordering | High-priority tasks are placed before lower-priority ones |
| 13 | Empty pet | A pet with no tasks returns empty lists without errors |
| 14 | Filter by status | `filter_tasks(completed=True/False)` returns only matching tasks |
| 15 | Filter by pet name | `filter_tasks(pet_name=...)` isolates a single pet's tasks |

### Confidence level

★★★★☆ (4/5) — All 15 tests pass. Happy paths and the most important edge cases (empty pets, no slots, overflow tasks, adjacent-vs-overlapping conflicts, recurrence) are covered. The remaining gap is integration-level testing of the full Streamlit UI and multi-day recurrence chains, which would require additional end-to-end tooling.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
