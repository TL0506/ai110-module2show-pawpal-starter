# PawPal+

**PawPal+** is a Streamlit-based daily pet-care planner that helps a busy owner stay consistent with pet tasks. Given a list of pets, care activities, and available free time, it generates a priority-ordered schedule, warns about conflicts, and automatically queues the next occurrence of recurring tasks.

---

## Features

### Core scheduling

| Feature | What it does |
|---|---|
| **Priority-based scheduling** | Pets and tasks are both ranked by priority. The scheduler processes pets from highest to lowest priority (`Pet.priority`), and within each pet processes tasks from `high` → `medium` → `low`. This ensures critical tasks (e.g., medication) always claim the first available slot. |
| **First-fit slot assignment** | For each pending task, `Scheduler._find_slot()` scans the owner's free `TimeSlot`s in order and assigns the first one that is both unoccupied and wide enough (`TimeSlot.can_fit()`). Tasks that cannot fit any slot are recorded in `DailySchedule.unscheduled_tasks` so nothing is silently dropped. |
| **Scheduling reasoning** | Every placed task is stored as a `ScheduledTask` with a human-readable `reasoning` string explaining why it was prioritized (e.g., "Buddy has priority 1; high-priority task scheduled first; medication is time-sensitive"). |

### Algorithmic features

| Feature | Method | Algorithm |
|---|---|---|
| **Chronological sort** | `Scheduler.sort_by_time()` | Uses Python's `sorted()` with a `lambda` key that parses each task's `start_time` string via `datetime.strptime(…, "%H:%M")`, producing a correctly ordered list regardless of insertion order. |
| **Task filtering** | `Scheduler.filter_tasks(completed, pet_name)` | Iterates all `(Pet, Task)` pairs and applies two independent predicates — completion status and pet name — allowing any combination of filters (e.g., all pending tasks for a single pet). |
| **Daily recurrence** | `Scheduler.mark_task_complete()` + `_spawn_next_occurrence()` | When a `DAILY` or `TWICE_DAILY` task is marked done, `_spawn_next_occurrence()` computes the next due date using Python's `timedelta(days=1)` and appends a new `Task` clone to the pet. `WEEKLY` tasks use `timedelta(days=7)`. `AS_NEEDED` tasks are never auto-spawned. |
| **Conflict detection** | `Scheduler.detect_conflicts()` | Performs an O(n²) pairwise scan over all scheduled tasks and applies the standard interval-overlap test: `a.start < b.end AND b.start < a.end`. Overlapping pairs produce a human-readable warning string instead of raising an exception, so the UI can surface warnings without crashing. |

### UI features (Streamlit)

- **Owner setup** — enter your name to begin a session persisted in `st.session_state`.
- **Multi-pet support** — add any number of pets with name, breed, species, and priority.
- **Task management** — add care tasks to any pet with type, description, duration, priority, and frequency.
- **Free-time calendar** — define available time blocks in `HH:MM` format; total free minutes are displayed.
- **Live schedule view** — tasks are displayed in a sortable dataframe ordered chronologically.
- **Conflict banners** — overlapping time slots surface as inline Streamlit error/warning messages.
- **Pending task tracker** — an expandable section lists every task still incomplete after the plan runs.

---

## 📸 Demo

<a href="/course_images/ai110/demo.png" target="_blank"><img src='/course_images/ai110/demo.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## Getting started

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Usage walkthrough

1. **Owner setup** (Section 1) — enter your name and click **Set owner**.
2. **Add pets** (Section 2) — fill in name, breed, species, and priority (1 = most important), then click **Add pet**.
3. **Add care tasks** (Section 3) — select a pet, pick a task type and frequency, set duration and priority, then click **Add task**.
4. **Set free time** (Section 4) — add one or more time blocks in `HH:MM` format.
5. **Generate schedule** (Section 5) — pick a date and click **Generate schedule**. The app displays:
   - Any conflict warnings at the top
   - Scheduled tasks in chronological order with reasoning
   - Unscheduled tasks (if any) with an explanation
   - Still-pending tasks in a collapsible panel

---

## Project structure

```
pawpal_system.py   — domain model and scheduler logic (Owner, Pet, Task, Scheduler, …)
app.py             — Streamlit UI
tests/
  test_pawpal.py   — 15-test automated suite
requirements.txt
```

---

## Testing

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
| 15 | Filter by pet name | `filter_tasks(pet_name=…)` isolates a single pet's tasks |

### Confidence level

★★★★☆ (4/5) — All 15 tests pass. Happy paths and the most important edge cases (empty pets, no slots, overflow tasks, adjacent-vs-overlapping conflicts, recurrence) are covered. The remaining gap is integration-level testing of the full Streamlit UI and multi-day recurrence chains, which would require additional end-to-end tooling.

---

## Architecture overview

The system is modelled as a hierarchy of dataclasses with a clear single-responsibility split:

```
Owner  ──owns──►  Pet  ──has──►  Task
  │                                │
  └──available_time──►  TimeSlot   └── TaskType (enum)
                                   └── Frequency (enum)

Scheduler  ──uses──►  Owner
           ──produces──►  DailySchedule  ──contains──►  ScheduledTask
```

The `Scheduler` is the only class that reads across the full object graph. All other classes manage only their own state, making the logic easy to test in isolation.
