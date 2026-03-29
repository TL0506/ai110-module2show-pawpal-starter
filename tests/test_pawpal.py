"""
PawPal+ automated test suite.

Core behaviors verified:
  1. Task completion         — complete() flips is_completed
  2. Task addition           — add_task() grows the pet's task list
  3. Sort by time            — sort_by_time() returns tasks chronologically
  4. Recurrence (daily)      — marking done spawns a +1-day occurrence
  5. Recurrence (weekly)     — marking done spawns a +7-day occurrence
  6. No recurrence (AS_NEEDED) — marking done does NOT spawn anything
  7. Conflict detection      — overlapping slots produce a warning
  8. No false conflicts      — adjacent (back-to-back) slots are not flagged
  9. No available slots      — all tasks land in unscheduled_tasks
 10. Task too long for slot  — oversized task lands in unscheduled_tasks
 11. Priority ordering       — high-priority task is scheduled before low
 12. Pet with no tasks       — edge case: empty pet is handled gracefully
 13. Filter by completion    — filter_tasks(completed=True/False) works
 14. Filter by pet name      — filter_tasks(pet_name=...) isolates one pet
"""

import pytest
from pawpal_system import (
    Owner, Pet, Task, TaskType, Frequency,
    TimeSlot, Scheduler, ScheduledTask, DailySchedule,
)


# ==================================================================
# Fixtures
# ==================================================================

@pytest.fixture
def sample_task():
    """A basic walking task, starts incomplete."""
    return Task(
        task_type=TaskType.WALKING,
        description="Morning walk",
        duration_minutes=30,
        priority="medium",
        frequency=Frequency.DAILY,
    )


@pytest.fixture
def sample_pet():
    """A dog with no tasks yet."""
    return Pet(name="Buddy", breed="Golden Retriever", type="dog", priority=1)


@pytest.fixture
def simple_owner():
    """Owner with two free slots and one dog that has two tasks."""
    owner = Owner(name="Alex")
    owner.set_availability([
        TimeSlot("07:00", "07:20"),   # 20 min
        TimeSlot("08:00", "08:45"),   # 45 min
    ])
    dog = Pet(name="Rex", breed="Labrador", type="dog", priority=1)
    dog.add_task(Task(TaskType.MEDICATION, "Morning pill",   5,  "high",   Frequency.DAILY, due_date="2026-03-28"))
    dog.add_task(Task(TaskType.WALKING,    "Park walk",      30, "medium", Frequency.DAILY, due_date="2026-03-28"))
    owner.add_pet(dog)
    return owner


# ==================================================================
# 1. Task Completion
# ==================================================================

def test_task_completion_changes_status(sample_task):
    """complete() should flip is_completed from False to True."""
    assert sample_task.is_completed is False
    sample_task.complete()
    assert sample_task.is_completed is True


# ==================================================================
# 2. Task Addition
# ==================================================================

def test_adding_task_increases_pet_task_count(sample_pet, sample_task):
    """add_task() should increase the pet's task list by exactly one."""
    before = len(sample_pet.get_tasks())
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == before + 1


# ==================================================================
# 3. Sort by time
# ==================================================================

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should reorder tasks from earliest to latest start time."""
    owner = Owner(name="Test")
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    scheduler = Scheduler(owner=owner)

    # Build a schedule with tasks added in REVERSE chronological order
    late_slot  = TimeSlot("17:00", "17:30")
    early_slot = TimeSlot("07:00", "07:20")

    schedule = DailySchedule(date="2026-03-28")
    schedule.add_scheduled_task(ScheduledTask(
        task=Task(TaskType.GROOMING,   "Evening brush", 10, "low"),
        pet=pet, time_slot=late_slot,
    ))
    schedule.add_scheduled_task(ScheduledTask(
        task=Task(TaskType.MEDICATION, "Morning pill",   5, "high"),
        pet=pet, time_slot=early_slot,
    ))
    scheduler.schedule = schedule

    sorted_tasks = scheduler.sort_by_time()

    assert sorted_tasks[0].time_slot.start_time == "07:00"
    assert sorted_tasks[1].time_slot.start_time == "17:00"


def test_sort_by_time_on_empty_schedule_returns_empty_list():
    """sort_by_time() should return [] when no tasks have been scheduled."""
    owner = Owner(name="Test")
    scheduler = Scheduler(owner=owner)
    scheduler.schedule = DailySchedule(date="2026-03-28")
    assert scheduler.sort_by_time() == []


# ==================================================================
# 4. Recurrence — daily task
# ==================================================================

def test_daily_task_recurrence_creates_next_day_occurrence():
    """Marking a DAILY task complete should add a new task due the next day."""
    owner = Owner(name="Test")
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    pet.add_task(Task(
        task_type=TaskType.FEEDING,
        description="Breakfast",
        duration_minutes=10,
        priority="high",
        frequency=Frequency.DAILY,
        due_date="2026-03-28",
    ))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    result = scheduler.mark_task_complete("Rex", TaskType.FEEDING)

    assert result is True
    feeding_tasks = pet.get_tasks_by_type(TaskType.FEEDING)
    assert len(feeding_tasks) == 2                            # original + new

    new_task = next(t for t in feeding_tasks if not t.is_completed)
    assert new_task.due_date == "2026-03-29"                  # +1 day via timedelta


# ==================================================================
# 5. Recurrence — weekly task
# ==================================================================

def test_weekly_task_recurrence_creates_seven_day_occurrence():
    """Marking a WEEKLY task complete should add a new task due 7 days later."""
    owner = Owner(name="Test")
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    pet.add_task(Task(
        task_type=TaskType.GROOMING,
        description="Weekly brush",
        duration_minutes=10,
        priority="low",
        frequency=Frequency.WEEKLY,
        due_date="2026-03-28",
    ))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.mark_task_complete("Rex", TaskType.GROOMING)

    grooming_tasks = pet.get_tasks_by_type(TaskType.GROOMING)
    new_task = next(t for t in grooming_tasks if not t.is_completed)
    assert new_task.due_date == "2026-04-04"                  # +7 days via timedelta


# ==================================================================
# 6. No recurrence — AS_NEEDED task
# ==================================================================

def test_as_needed_task_does_not_spawn_new_occurrence():
    """Marking an AS_NEEDED task complete should NOT create a follow-up task."""
    owner = Owner(name="Test")
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    pet.add_task(Task(
        task_type=TaskType.GROOMING,
        description="One-off groom",
        duration_minutes=10,
        priority="low",
        frequency=Frequency.AS_NEEDED,
        due_date="2026-03-28",
    ))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.mark_task_complete("Rex", TaskType.GROOMING)

    assert len(pet.get_tasks_by_type(TaskType.GROOMING)) == 1  # still just one


# ==================================================================
# 7. Conflict detection — overlapping slots
# ==================================================================

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap should produce a conflict warning."""
    owner = Owner(name="Test")
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    scheduler = Scheduler(owner=owner)

    slot_a = TimeSlot("09:00", "09:30")
    slot_b = TimeSlot("09:15", "09:45")   # overlaps slot_a by 15 min

    schedule = DailySchedule(date="2026-03-28")
    schedule.add_scheduled_task(ScheduledTask(
        task=Task(TaskType.WALKING,  "Walk",  30, "medium"), pet=pet, time_slot=slot_a,
    ))
    schedule.add_scheduled_task(ScheduledTask(
        task=Task(TaskType.FEEDING, "Feed", 30, "high"), pet=pet, time_slot=slot_b,
    ))
    scheduler.schedule = schedule

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "CONFLICT" in conflicts[0]


# ==================================================================
# 8. No false conflicts — adjacent (back-to-back) slots
# ==================================================================

def test_detect_conflicts_no_warning_for_adjacent_slots():
    """Tasks that end exactly when the next begins should NOT be flagged."""
    owner = Owner(name="Test")
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    scheduler = Scheduler(owner=owner)

    slot_a = TimeSlot("09:00", "09:30")
    slot_b = TimeSlot("09:30", "10:00")   # starts exactly when slot_a ends

    schedule = DailySchedule(date="2026-03-28")
    schedule.add_scheduled_task(ScheduledTask(
        task=Task(TaskType.WALKING,  "Walk", 30, "medium"), pet=pet, time_slot=slot_a,
    ))
    schedule.add_scheduled_task(ScheduledTask(
        task=Task(TaskType.FEEDING, "Feed", 30, "high"),   pet=pet, time_slot=slot_b,
    ))
    scheduler.schedule = schedule

    assert scheduler.detect_conflicts() == []


# ==================================================================
# 9. Edge case — no available slots
# ==================================================================

def test_scheduler_with_no_slots_places_all_tasks_in_unscheduled():
    """When the owner has no free time, every task should land in unscheduled_tasks."""
    owner = Owner(name="Test")   # no time slots added
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    pet.add_task(Task(TaskType.FEEDING, "Breakfast", 10, "high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_daily_plan("2026-03-28")

    assert len(plan.scheduled_tasks) == 0
    assert len(plan.unscheduled_tasks) == 1


# ==================================================================
# 10. Edge case — task too long for available slot
# ==================================================================

def test_task_longer_than_slot_goes_to_unscheduled():
    """A task that doesn't fit in any available slot should be unscheduled."""
    owner = Owner(name="Test")
    owner.add_time_slot(TimeSlot("08:00", "08:10"))   # only 10 minutes free
    pet = Pet(name="Rex", breed="Lab", type="dog", priority=1)
    pet.add_task(Task(TaskType.WALKING, "Long walk", 60, "high"))   # needs 60 min
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_daily_plan("2026-03-28")

    assert len(plan.scheduled_tasks) == 0
    assert len(plan.unscheduled_tasks) == 1


# ==================================================================
# 11. Priority ordering
# ==================================================================

def test_high_priority_task_scheduled_before_low_priority(simple_owner):
    """The scheduler should place high-priority tasks first within a pet."""
    scheduler = Scheduler(owner=simple_owner)
    plan = scheduler.generate_daily_plan("2026-03-28")

    assert len(plan.scheduled_tasks) >= 1
    # First task placed should be medication (high priority), not walking (medium)
    assert plan.scheduled_tasks[0].task.task_type == TaskType.MEDICATION


# ==================================================================
# 12. Edge case — pet with no tasks
# ==================================================================

def test_pet_with_no_tasks_returns_empty_lists():
    """A pet that has no tasks should return empty lists without errors."""
    pet = Pet(name="Empty", breed="Poodle", type="dog", priority=1)
    assert pet.get_tasks() == []
    assert pet.get_pending_tasks() == []
    assert pet.get_total_care_time() == 0


# ==================================================================
# 13. Filter by completion status
# ==================================================================

def test_filter_tasks_by_completed_status(simple_owner):
    """filter_tasks(completed=True) should return only finished tasks."""
    scheduler = Scheduler(owner=simple_owner)
    scheduler.generate_daily_plan("2026-03-28")   # marks tasks complete

    done   = scheduler.filter_tasks(completed=True)
    pending = scheduler.filter_tasks(completed=False)

    assert all(t.is_completed for _, t in done)
    assert all(not t.is_completed for _, t in pending)


# ==================================================================
# 14. Filter by pet name
# ==================================================================

def test_filter_tasks_by_pet_name():
    """filter_tasks(pet_name=...) should return only that pet's tasks."""
    owner = Owner(name="Test")
    dog = Pet(name="Buddy", breed="Lab",    type="dog", priority=1)
    cat = Pet(name="Luna",  breed="Siamese", type="cat", priority=2)

    dog.add_task(Task(TaskType.WALKING, "Walk",     30, "medium"))
    cat.add_task(Task(TaskType.FEEDING, "Wet food",  5, "high"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner=owner)
    buddy_tasks = scheduler.filter_tasks(pet_name="Buddy")
    luna_tasks  = scheduler.filter_tasks(pet_name="Luna")

    assert len(buddy_tasks) == 1
    assert buddy_tasks[0][0].name == "Buddy"
    assert len(luna_tasks) == 1
    assert luna_tasks[0][0].name == "Luna"
