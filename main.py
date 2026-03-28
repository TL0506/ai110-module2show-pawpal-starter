from pawpal_system import (
    Owner, Pet, Task, TaskType, Frequency, TimeSlot, Scheduler
)

# ------------------------------------------------------------------
# 1. Create Owner with available time slots
# ------------------------------------------------------------------
owner = Owner(name="Alex")
owner.set_availability([
    TimeSlot("07:00", "07:20"),   # 20-min slot — morning
    TimeSlot("08:00", "08:45"),   # 45-min slot — breakfast window
    TimeSlot("12:00", "12:30"),   # 30-min slot — midday
    TimeSlot("17:00", "17:30"),   # 30-min slot — after work
    TimeSlot("19:00", "19:15"),   # 15-min slot — evening
])
owner.set_preferences(["prefer outdoor tasks in the morning", "medication always first"])

# ------------------------------------------------------------------
# 2. Create Pets
# ------------------------------------------------------------------
buddy = Pet(name="Buddy", breed="Golden Retriever", type="dog", priority=1)
luna  = Pet(name="Luna",  breed="Siamese",          type="cat", priority=2)

# ------------------------------------------------------------------
# 3. Add Tasks (varied durations and priorities)
# ------------------------------------------------------------------

# Buddy's tasks
buddy.add_task(Task(
    task_type=TaskType.MEDICATION,
    description="Heartworm pill — give with food",
    duration_minutes=5,
    priority="high",
    frequency=Frequency.DAILY,
))
buddy.add_task(Task(
    task_type=TaskType.FEEDING,
    description="Breakfast — 2 cups dry kibble",
    duration_minutes=10,
    priority="high",
    frequency=Frequency.TWICE_DAILY,
))
buddy.add_task(Task(
    task_type=TaskType.WALKING,
    description="Morning walk around the park",
    duration_minutes=30,
    priority="medium",
    frequency=Frequency.DAILY,
))
buddy.add_task(Task(
    task_type=TaskType.GROOMING,
    description="Brush coat — 10 minutes",
    duration_minutes=10,
    priority="low",
    frequency=Frequency.WEEKLY,
))

# Luna's tasks
luna.add_task(Task(
    task_type=TaskType.FEEDING,
    description="Wet food — half a can",
    duration_minutes=5,
    priority="high",
    frequency=Frequency.TWICE_DAILY,
))
luna.add_task(Task(
    task_type=TaskType.ENRICHMENT,
    description="Feather wand play session",
    duration_minutes=15,
    priority="medium",
    frequency=Frequency.DAILY,
))
luna.add_task(Task(
    task_type=TaskType.GROOMING,
    description="Comb fur and check ears",
    duration_minutes=10,
    priority="low",
    frequency=Frequency.WEEKLY,
))

# Register pets with owner
owner.add_pet(buddy)
owner.add_pet(luna)

# ------------------------------------------------------------------
# 4. Run the Scheduler and print Today's Schedule
# ------------------------------------------------------------------
scheduler = Scheduler(owner=owner)
plan = scheduler.generate_daily_plan(date="2026-03-28")

print("=" * 55)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 55)
print(scheduler.explain_plan())

print()
print("-" * 55)
print("OWNER SUMMARY")
print("-" * 55)
print(owner)
print(f"Total pets    : {len(owner.pets)}")
print(f"Total tasks   : {len(owner.get_all_tasks())}")
print(f"Still pending : {len(scheduler.get_pending_tasks())}")
