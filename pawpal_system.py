from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# -------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------

class TaskType(Enum):
    WALKING = "walking"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


# -------------------------------------------------------------------
# Core data classes
# -------------------------------------------------------------------

@dataclass
class TimeSlot:
    start_time: str          # e.g. "08:00"
    end_time: str            # e.g. "08:30"
    is_occupied: bool = False
    occupied_by: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Compute how many minutes this slot spans from start_time to end_time."""
        fmt = "%H:%M"
        delta = datetime.strptime(self.end_time, fmt) - datetime.strptime(self.start_time, fmt)
        return int(delta.total_seconds() // 60)

    def is_available(self) -> bool:
        return not self.is_occupied

    def can_fit(self, task_duration: int) -> bool:
        """Return True if this slot is free and long enough for the given duration."""
        return self.is_available() and self.duration_minutes >= task_duration

    def block(self, reason: str) -> None:
        self.is_occupied = True
        self.occupied_by = reason


@dataclass
class Task:
    task_type: TaskType
    duration_minutes: int
    priority: str            # e.g. "high", "medium", "low"
    is_completed: bool = False

    def complete(self) -> None:
        self.is_completed = True

    def get_details(self) -> str:
        return (
            f"{self.task_type.value} | {self.duration_minutes} min | "
            f"priority: {self.priority} | done: {self.is_completed}"
        )


@dataclass
class Pet:
    name: str
    breed: str
    type: str                # e.g. "dog", "cat"
    priority: int            # lower number = higher priority
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        return self.tasks


@dataclass
class Owner:
    name: str
    available_time: list[TimeSlot] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def set_availability(self, slots: list[TimeSlot]) -> None:
        self.available_time = slots

    def set_preferences(self, prefs: list[str]) -> None:
        self.preferences = prefs


@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    time_slot: TimeSlot
    reasoning: str = ""

    def get_details(self) -> str:
        return (
            f"[{self.time_slot.start_time}-{self.time_slot.end_time}] "
            f"{self.pet.name}: {self.task.task_type.value} — {self.reasoning}"
        )


@dataclass
class DailySchedule:
    date: str                          # e.g. "2026-03-28"
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)   # tasks that couldn't be fit
    timeline: list[TimeSlot] = field(default_factory=list)

    def add_scheduled_task(self, task: ScheduledTask) -> None:
        self.scheduled_tasks.append(task)

    def get_timeline(self) -> list[TimeSlot]:
        return self.timeline

    def get_summary(self) -> str:
        if not self.scheduled_tasks:
            return "No tasks scheduled."
        lines = [f"Daily plan for {self.date}:"]
        for st in self.scheduled_tasks:
            lines.append(f"  {st.get_details()}")
        if self.unscheduled_tasks:
            lines.append("  [Could not schedule:]")
            for t in self.unscheduled_tasks:
                lines.append(f"    - {t.get_details()}")
        return "\n".join(lines)


# -------------------------------------------------------------------
# Scheduler
# -------------------------------------------------------------------

@dataclass
class Scheduler:
    owner: Owner
    schedule: DailySchedule = field(default_factory=lambda: DailySchedule(date=""))

    def generate_daily_plan(self, date: str) -> DailySchedule:
        """Create a fresh schedule for the given date and populate it."""
        self.schedule = DailySchedule(
            date=date,
            timeline=list(self.owner.available_time),  # seed timeline from owner's free slots
        )
        # TODO: implement scheduling logic
        return self.schedule

    def apply_constraints(self) -> None:
        # TODO: filter available time slots against owner's occupied times
        pass

    def rank_by_priority(self, pets: list[Pet]) -> list[Pet]:
        return sorted(pets, key=lambda p: p.priority)

    def explain_plan(self) -> str:
        return self.schedule.get_summary()
