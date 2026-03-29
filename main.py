from pawpal_system import (
    Owner, Pet, Task, TaskType, Frequency, TimeSlot, Scheduler, ScheduledTask, DailySchedule
)

SEP  = "=" * 60
SEP2 = "-" * 60

# ------------------------------------------------------------------
# Setup — owner, pets, time slots
# ------------------------------------------------------------------
owner = Owner(name="Alex")
owner.set_availability([
    TimeSlot("07:00", "07:20"),
    TimeSlot("08:00", "08:45"),
    TimeSlot("12:00", "12:30"),
    TimeSlot("17:00", "17:30"),
    TimeSlot("19:00", "19:15"),
])
owner.set_preferences(["medication always first", "prefer outdoor tasks in the morning"])

buddy = Pet(name="Buddy", breed="Golden Retriever", type="dog", priority=1)
luna  = Pet(name="Luna",  breed="Siamese",          type="cat", priority=2)

# Tasks added OUT OF ORDER intentionally (to demo sort_by_time)
buddy.add_task(Task(TaskType.WALKING,    "Morning walk",          30, "medium", Frequency.DAILY,       due_date="2026-03-28"))
buddy.add_task(Task(TaskType.MEDICATION, "Heartworm pill",         5, "high",   Frequency.DAILY,       due_date="2026-03-28"))
buddy.add_task(Task(TaskType.FEEDING,    "Breakfast kibble",      10, "high",   Frequency.TWICE_DAILY, due_date="2026-03-28"))
buddy.add_task(Task(TaskType.GROOMING,   "Brush coat",            10, "low",    Frequency.WEEKLY,      due_date="2026-03-28"))

luna.add_task(Task(TaskType.GROOMING,    "Comb fur and check ears",10, "low",   Frequency.WEEKLY,      due_date="2026-03-28"))
luna.add_task(Task(TaskType.ENRICHMENT,  "Feather wand play",     15, "medium", Frequency.DAILY,       due_date="2026-03-28"))
luna.add_task(Task(TaskType.FEEDING,     "Wet food half-can",      5, "high",   Frequency.TWICE_DAILY, due_date="2026-03-28"))

owner.add_pet(buddy)
owner.add_pet(luna)

scheduler = Scheduler(owner=owner)

# ------------------------------------------------------------------
# 1. Today's Schedule
# ------------------------------------------------------------------
plan = scheduler.generate_daily_plan(date="2026-03-28")

print(SEP)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print(SEP)
print(scheduler.explain_plan())

# ------------------------------------------------------------------
# 2. Sort by time  (tasks were added out of order above)
# ------------------------------------------------------------------
print()
print(SEP)
print("  SORTED BY START TIME  (sort_by_time)")
print(SEP)
for entry in scheduler.sort_by_time():
    print(f"  {entry.get_details()}")

# ------------------------------------------------------------------
# 3. Filter tasks
# ------------------------------------------------------------------
print()
print(SEP)
print("  FILTER: completed tasks across all pets")
print(SEP)
done = scheduler.filter_tasks(completed=True)
if done:
    for pet, task in done:
        print(f"  [{pet.name}] {task.get_details()}")
else:
    print("  (none)")

print()
print(SEP)
print("  FILTER: pending tasks for Luna only")
print(SEP)
luna_pending = scheduler.filter_tasks(completed=False, pet_name="Luna")
if luna_pending:
    for pet, task in luna_pending:
        print(f"  [{pet.name}] {task.get_details()}")
else:
    print("  (none)")

# ------------------------------------------------------------------
# 4. Recurring task — mark complete and verify next occurrence spawns
# ------------------------------------------------------------------
print()
print(SEP)
print("  RECURRING TASK — mark Buddy's evening feeding complete")
print(SEP)
# Add a fresh pending feeding task (the morning one was already completed by the scheduler)
buddy.add_task(Task(TaskType.FEEDING, "Evening kibble", 10, "high", Frequency.DAILY, due_date="2026-03-28"))
buddy_feeding_before = len(buddy.get_tasks_by_type(TaskType.FEEDING))
scheduler.mark_task_complete("Buddy", TaskType.FEEDING)   # finds the new pending task
buddy_feeding_after = len(buddy.get_tasks_by_type(TaskType.FEEDING))
print(f"  Feeding tasks before mark_complete : {buddy_feeding_before}")
print(f"  Feeding tasks after  mark_complete : {buddy_feeding_after}  ← next occurrence auto-added via timedelta")
for t in buddy.get_tasks_by_type(TaskType.FEEDING):
    print(f"    → {t.get_details()}")

# ------------------------------------------------------------------
# 5. Conflict detection — manually inject two overlapping tasks
# ------------------------------------------------------------------
print()
print(SEP)
print("  CONFLICT DETECTION")
print(SEP)

# Build a fake schedule with two tasks that overlap: 09:00-09:30 and 09:15-09:45
conflict_schedule = DailySchedule(date="2026-03-28")
slot_a = TimeSlot("09:00", "09:30")
slot_b = TimeSlot("09:15", "09:45")   # overlaps slot_a by 15 minutes

conflict_schedule.add_scheduled_task(ScheduledTask(
    task=Task(TaskType.WALKING,  "Morning walk",  30, "medium"),
    pet=buddy,
    time_slot=slot_a,
    reasoning="manual test",
))
conflict_schedule.add_scheduled_task(ScheduledTask(
    task=Task(TaskType.ENRICHMENT, "Play session", 30, "low"),
    pet=luna,
    time_slot=slot_b,
    reasoning="manual test",
))

scheduler.schedule = conflict_schedule
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")

print()
print(SEP2)
print("All checks complete.")
print(SEP2)
