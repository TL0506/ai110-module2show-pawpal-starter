from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


# -------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------

class TaskType(Enum):
    WALKING    = "walking"
    FEEDING    = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING   = "grooming"


class Frequency(Enum):
    DAILY       = "daily"
    TWICE_DAILY = "twice_daily"
    WEEKLY      = "weekly"
    AS_NEEDED   = "as_needed"


PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}

# How many days ahead each frequency recurs
_RECUR_DAYS = {
    Frequency.DAILY:       1,
    Frequency.TWICE_DAILY: 1,
    Frequency.WEEKLY:      7,
}


# -------------------------------------------------------------------
# TimeSlot — owner's calendar block
# -------------------------------------------------------------------

@dataclass
class TimeSlot:
    start_time: str           # "HH:MM"
    end_time: str             # "HH:MM"
    is_occupied: bool = False
    occupied_by: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Minutes between start_time and end_time."""
        fmt = "%H:%M"
        delta = datetime.strptime(self.end_time, fmt) - datetime.strptime(self.start_time, fmt)
        return int(delta.total_seconds() // 60)

    def is_available(self) -> bool:
        """Return True if this slot has not been blocked."""
        return not self.is_occupied

    def can_fit(self, task_duration: int) -> bool:
        """True if this slot is free and wide enough for task_duration minutes."""
        return self.is_available() and self.duration_minutes >= task_duration

    def block(self, reason: str) -> None:
        """Mark this slot as occupied and record what is using it."""
        self.is_occupied = True
        self.occupied_by = reason


# -------------------------------------------------------------------
# Task — a single care activity
# -------------------------------------------------------------------

@dataclass
class Task:
    task_type: TaskType
    description: str          # human-readable label, e.g. "Morning walk around the block"
    duration_minutes: int     # how long this activity takes
    priority: str             # "high" | "medium" | "low"
    frequency: Frequency = Frequency.DAILY
    is_completed: bool = False
    due_date: Optional[str] = None   # "YYYY-MM-DD" — set when task is created or recurred

    # ------ state management ------

    def complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

    def reset(self) -> None:
        """Reset completion for a new day."""
        self.is_completed = False

    # ------ helpers ------

    @property
    def priority_rank(self) -> int:
        """Numeric rank so tasks can be sorted (lower = higher priority)."""
        return PRIORITY_ORDER.get(self.priority, 99)

    def get_details(self) -> str:
        """Return a single-line summary of this task's type, duration, priority, and status."""
        status = "done" if self.is_completed else "pending"
        due = f" | due {self.due_date}" if self.due_date else ""
        return (
            f"{self.task_type.value} | \"{self.description}\" | "
            f"{self.duration_minutes} min | {self.priority} priority | "
            f"{self.frequency.value}{due} | {status}"
        )


# -------------------------------------------------------------------
# Pet — stores pet identity and its care tasks
# -------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    breed: str
    type: str              # "dog", "cat", "rabbit", etc.
    priority: int          # 1 = most important; used by Scheduler to order pets

    tasks: list[Task] = field(default_factory=list)

    # ------ task management ------

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a specific task from this pet."""
        self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks regardless of status."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks not yet completed, sorted by priority."""
        pending = [t for t in self.tasks if not t.is_completed]
        return sorted(pending, key=lambda t: t.priority_rank)

    def get_tasks_by_type(self, task_type: TaskType) -> list[Task]:
        """Return all tasks of a given type."""
        return [t for t in self.tasks if t.task_type == task_type]

    def get_total_care_time(self) -> int:
        """Sum of duration_minutes across all pending tasks."""
        return sum(t.duration_minutes for t in self.tasks if not t.is_completed)

    def reset_daily_tasks(self) -> None:
        """Reset completion status on daily and twice-daily tasks for a new day."""
        for task in self.tasks:
            if task.frequency in (Frequency.DAILY, Frequency.TWICE_DAILY):
                task.reset()

    def __str__(self) -> str:
        """Return a readable one-line description of this pet."""
        return f"{self.name} ({self.breed}, {self.type}) — priority {self.priority}"


# -------------------------------------------------------------------
# Owner — manages pets and calendar availability
# -------------------------------------------------------------------

@dataclass
class Owner:
    name: str
    available_time: list[TimeSlot] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    # ------ pet management ------

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional["Pet"]:
        """Look up a pet by name; returns None if not found."""
        for p in self.pets:
            if p.name == pet_name:
                return p
        return None

    def get_pets_by_priority(self) -> list[Pet]:
        """Return pets sorted from highest to lowest priority."""
        return sorted(self.pets, key=lambda p: p.priority)

    # ------ cross-pet task access ------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Flat list of (pet, task) pairs across every owned pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Flat list of (pet, task) pairs for every pending task, sorted by pet priority then task priority."""
        pairs = [
            (pet, task)
            for pet in self.get_pets_by_priority()
            for task in pet.get_pending_tasks()
        ]
        return pairs

    def get_tasks_by_type(self, task_type: TaskType) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs where task matches the given type."""
        return [(pet, task) for pet, task in self.get_all_tasks() if task.task_type == task_type]

    # ------ availability management ------

    def set_availability(self, slots: list[TimeSlot]) -> None:
        """Replace the owner's available time slots."""
        self.available_time = slots

    def add_time_slot(self, slot: TimeSlot) -> None:
        """Add a single available time slot."""
        self.available_time.append(slot)

    def get_free_slots(self) -> list[TimeSlot]:
        """Return only the slots that are still unoccupied."""
        return [s for s in self.available_time if s.is_available()]

    def set_preferences(self, prefs: list[str]) -> None:
        """Replace the owner's care preference list."""
        self.preferences = prefs

    def __str__(self) -> str:
        """Return a one-line summary of the owner, their pets, and free slot count."""
        pet_names = ", ".join(p.name for p in self.pets) or "none"
        free = len(self.get_free_slots())
        return f"Owner: {self.name} | Pets: {pet_names} | Free slots: {free}"


# -------------------------------------------------------------------
# ScheduledTask — one resolved assignment in the final plan
# -------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    time_slot: TimeSlot
    reasoning: str = ""

    def get_details(self) -> str:
        """Return a formatted string showing the time, pet, task, and scheduling reason."""
        return (
            f"[{self.time_slot.start_time}–{self.time_slot.end_time}] "
            f"{self.pet.name}: {self.task.task_type.value} "
            f"(\"{self.task.description}\") — {self.reasoning}"
        )


# -------------------------------------------------------------------
# DailySchedule — the output of the Scheduler
# -------------------------------------------------------------------

@dataclass
class DailySchedule:
    date: str
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    unscheduled_tasks: list[tuple[Pet, Task]] = field(default_factory=list)  # couldn't fit
    timeline: list[TimeSlot] = field(default_factory=list)

    def add_scheduled_task(self, entry: ScheduledTask) -> None:
        """Append a successfully placed task to the schedule."""
        self.scheduled_tasks.append(entry)

    def add_unscheduled(self, pet: Pet, task: Task) -> None:
        """Record a task that could not be fit into any available slot."""
        self.unscheduled_tasks.append((pet, task))

    def get_timeline(self) -> list[TimeSlot]:
        """Return the list of time slots that make up this day's calendar."""
        return self.timeline

    def get_summary(self) -> str:
        """Return a formatted multi-line string of all scheduled and unscheduled tasks."""
        lines = [f"=== Daily plan for {self.date} ==="]
        if not self.scheduled_tasks:
            lines.append("  (no tasks could be scheduled)")
        else:
            for entry in self.scheduled_tasks:
                lines.append(f"  {entry.get_details()}")
        if self.unscheduled_tasks:
            lines.append("  --- Could NOT be scheduled (no free slot) ---")
            for pet, task in self.unscheduled_tasks:
                lines.append(f"    [{pet.name}] {task.get_details()}")
        return "\n".join(lines)


# -------------------------------------------------------------------
# Scheduler — the "brain"
# -------------------------------------------------------------------

@dataclass
class Scheduler:
    owner: Owner
    schedule: DailySchedule = field(default_factory=lambda: DailySchedule(date=""))

    # ------ main entry point ------

    def generate_daily_plan(self, date: str) -> DailySchedule:
        """
        Build a complete DailySchedule for `date`.

        Algorithm:
          1. Reset recurring tasks on every pet.
          2. Copy the owner's free TimeSlots into the schedule's timeline.
          3. Walk pets in priority order; within each pet walk tasks in priority order.
          4. For each pending task, find the first free slot that fits it.
             - If found  → create ScheduledTask, block the slot.
             - If not    → add to unscheduled_tasks.
        """
        # Step 1 — fresh slate for all recurring tasks
        for pet in self.owner.pets:
            pet.reset_daily_tasks()

        # Step 2 — seed timeline from owner's free slots (copies so blocking is isolated)
        free_slots = [
            TimeSlot(s.start_time, s.end_time, s.is_occupied, s.occupied_by)
            for s in self.owner.available_time
            if s.is_available()
        ]
        self.schedule = DailySchedule(date=date, timeline=free_slots)

        # Step 3 & 4 — assign tasks
        for pet in self.owner.get_pets_by_priority():
            for task in pet.get_pending_tasks():
                slot = self._find_slot(task.duration_minutes)
                if slot:
                    reasoning = self._build_reasoning(pet, task)
                    slot.block(f"{pet.name}: {task.task_type.value}")
                    task.complete()
                    self.schedule.add_scheduled_task(
                        ScheduledTask(task=task, pet=pet, time_slot=slot, reasoning=reasoning)
                    )
                else:
                    self.schedule.add_unscheduled(pet, task)

        return self.schedule

    # ------ sorting ------

    def sort_by_time(self) -> list[ScheduledTask]:
        """Return scheduled tasks sorted chronologically by their start time (HH:MM)."""
        return sorted(
            self.schedule.scheduled_tasks,
            key=lambda st: datetime.strptime(st.time_slot.start_time, "%H:%M"),
        )

    # ------ filtering ------

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Filter all tasks across every pet by completion status and/or pet name.

        Parameters
        ----------
        completed : True  → only done tasks
                    False → only pending tasks
                    None  → all tasks (no filter)
        pet_name  : restrict results to a single named pet; None means all pets
        """
        pairs = self.owner.get_all_tasks()
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name == pet_name]
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.is_completed == completed]
        return pairs

    # ------ conflict detection ------

    def detect_conflicts(self) -> list[str]:
        """
        Check the current schedule for overlapping time slots.

        Two scheduled tasks conflict when their time windows overlap:
            task_a.start < task_b.end  AND  task_b.start < task_a.end

        Returns a list of human-readable warning strings (empty if no conflicts).
        This is intentionally a warning rather than an exception so the
        caller can decide how to handle it.
        """
        fmt = "%H:%M"
        warnings: list[str] = []
        entries = self.schedule.scheduled_tasks

        for i, a in enumerate(entries):
            for b in entries[i + 1:]:
                a_start = datetime.strptime(a.time_slot.start_time, fmt)
                a_end   = datetime.strptime(a.time_slot.end_time,   fmt)
                b_start = datetime.strptime(b.time_slot.start_time, fmt)
                b_end   = datetime.strptime(b.time_slot.end_time,   fmt)

                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"⚠  CONFLICT: {a.pet.name}/{a.task.task_type.value} "
                        f"[{a.time_slot.start_time}–{a.time_slot.end_time}] overlaps "
                        f"{b.pet.name}/{b.task.task_type.value} "
                        f"[{b.time_slot.start_time}–{b.time_slot.end_time}]"
                    )
        return warnings

    # ------ constraint helpers ------

    def apply_constraints(self) -> None:
        """
        Block any timeline slots that overlap with already-occupied owner slots.
        Call this before generate_daily_plan if the owner's calendar has pre-existing blocks.
        """
        for slot in self.schedule.timeline:
            for owner_slot in self.owner.available_time:
                if owner_slot.is_occupied and owner_slot.start_time == slot.start_time:
                    slot.block(owner_slot.occupied_by or "owner busy")

    def _find_slot(self, duration_minutes: int) -> Optional[TimeSlot]:
        """Return the first timeline slot that is free and long enough."""
        for slot in self.schedule.timeline:
            if slot.can_fit(duration_minutes):
                return slot
        return None

    def _build_reasoning(self, pet: Pet, task: Task) -> str:
        """Explain why this task was placed where it was."""
        reasons = [f"{pet.name} has priority {pet.priority}"]
        if task.priority == "high":
            reasons.append("high-priority task scheduled first")
        if task.task_type == TaskType.MEDICATION:
            reasons.append("medication is time-sensitive")
        return "; ".join(reasons)

    # ------ recurring task helpers ------

    def _spawn_next_occurrence(self, pet: Pet, completed_task: Task) -> None:
        """
        After a recurring task is marked complete, add its next occurrence to the pet.

        Uses timedelta to calculate the next due date:
          daily / twice_daily → today + 1 day
          weekly              → today + 7 days
          as_needed           → no automatic recurrence
        """
        days = _RECUR_DAYS.get(completed_task.frequency)
        if days is None:
            return  # AS_NEEDED — do not auto-schedule

        base = (
            datetime.strptime(completed_task.due_date, "%Y-%m-%d")
            if completed_task.due_date
            else datetime.today()
        )
        next_due = (base + timedelta(days=days)).strftime("%Y-%m-%d")

        pet.add_task(Task(
            task_type=completed_task.task_type,
            description=completed_task.description,
            duration_minutes=completed_task.duration_minutes,
            priority=completed_task.priority,
            frequency=completed_task.frequency,
            due_date=next_due,
        ))

    # ------ query / mutation methods ------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """All (pet, task) pairs across every pet the owner has."""
        return self.owner.get_all_tasks()

    def get_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """All incomplete (pet, task) pairs, ordered by pet priority then task priority."""
        return self.owner.get_all_pending_tasks()

    def get_tasks_by_type(self, task_type: TaskType) -> list[tuple[Pet, Task]]:
        """Find all tasks of a specific type across all pets."""
        return self.owner.get_tasks_by_type(task_type)

    def mark_task_complete(self, pet_name: str, task_type: TaskType) -> bool:
        """
        Mark the first matching pending task complete and spawn its next occurrence.

        For daily / twice_daily / weekly tasks, a new Task is automatically added
        to the pet with a due_date calculated via timedelta from today.
        Returns True if a task was found and marked, False otherwise.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.get_tasks_by_type(task_type):
            if not task.is_completed:
                task.complete()
                self._spawn_next_occurrence(pet, task)
                return True
        return False

    def rank_by_priority(self, pets: list[Pet]) -> list[Pet]:
        """Return the given pet list sorted from highest to lowest priority."""
        return sorted(pets, key=lambda p: p.priority)

    def explain_plan(self) -> str:
        """Print the full summary of the current schedule."""
        return self.schedule.get_summary()
