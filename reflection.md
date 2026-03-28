# PawPal+ Project Reflection

## 1. System Design
- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
    Create Pet
        Hold a name for the pet and what breed the pet is/ what it is
    Today's schedule/Task
    List of all the time what is occupied in the time and what task it is

    Make them do pet care tasks/schedule -- creates the task/ scheduling the task below
        walking
        Feeding
        meds
        enrichment
        gromming
- Consider constraints (time available, priority, owner preferences)
    Time avaliable of Owner
    Priority of pet to take care of first
    Owner preference of how they want their pet to be taken care of
- Produce a daily plan and explain why it chose that plan

**a. Initial design**

The initial design used seven classes organized around an Owner who owns Pets, each Pet holding a list of Tasks, and a Scheduler that produces a DailySchedule.

| Class | Responsibility |
|---|---|
| `TaskType` | Enum listing the five care categories (walking, feeding, medication, enrichment, grooming) so task types are never raw strings |
| `TimeSlot` | Represents one block of the owner's day; tracks whether it is occupied and by what |
| `Task` | A single care action for a pet — stores the type, how long it takes, and its priority |
| `Pet` | Holds a pet's identity (name, breed, species) and its numeric priority relative to other pets; owns a list of Tasks |
| `Owner` | Central user object — stores the owner's name, their free TimeSlots, their care preferences, and the pets they own |
| `ScheduledTask` | A resolved assignment linking one Task to one Pet and one TimeSlot; also stores a `reasoning` string so the plan can explain itself |
| `DailySchedule` | The output artifact — an ordered list of ScheduledTasks for a given date, plus a summary printer |
| `Scheduler` | Orchestrator — reads the Owner's constraints, ranks pets by priority, fits tasks into available TimeSlots, and returns a DailySchedule |

**b. Design changes**

Yes, three changes were made after an AI code review of the skeleton.

1. **Added `duration_minutes` property and `can_fit()` to `TimeSlot`.**
   The original `TimeSlot` stored `start_time` and `end_time` as plain strings but had no way to compute how long the window actually was. Without this, the Scheduler could never check whether a `Task.duration_minutes` would fit inside a slot before assigning it — a logic bottleneck that would have caused incorrect scheduling. The fix parses the two time strings with `datetime.strptime` and exposes both the computed duration and a `can_fit(task_duration)` helper.

2. **Added `unscheduled_tasks` list to `DailySchedule`.**
   If the owner's day is too full to fit every pet task, the original design had nowhere to put the overflow. Tasks would silently be skipped with no record. Adding `unscheduled_tasks: list[Task]` makes gaps in the plan visible and lets the summary explain what was left out.

3. **Added a `date` parameter to `generate_daily_plan()`.**
   The original `Scheduler.schedule` defaulted to `DailySchedule(date="")`, meaning the date was never properly set unless the caller remembered to set it manually. The fix makes `date` an explicit parameter of `generate_daily_plan()`, which now creates a fresh `DailySchedule` with the correct date and seeds its timeline directly from `owner.available_time`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
