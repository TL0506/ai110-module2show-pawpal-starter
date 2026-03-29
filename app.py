import streamlit as st
from pawpal_system import (
    Owner, Pet, Task, TaskType, Frequency, TimeSlot, Scheduler
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner — priority-based, conflict-aware, and recurring-task ready.")

# ------------------------------------------------------------------
# Session state vault
# ------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None
if "last_scheduler" not in st.session_state:
    st.session_state.last_scheduler = None

# ------------------------------------------------------------------
# Section A — Owner setup
# ------------------------------------------------------------------
st.subheader("1. Owner Setup")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    if st.form_submit_button("Set owner"):
        if st.session_state.owner is None:
            st.session_state.owner = Owner(name=owner_name)
        else:
            st.session_state.owner.name = owner_name

if st.session_state.owner is None:
    st.info("Submit your name above to get started.")

# ------------------------------------------------------------------
# All remaining sections require an owner
# ------------------------------------------------------------------
if st.session_state.owner is not None:
    owner: Owner = st.session_state.owner
    st.success(f"Welcome, **{owner.name}**! Use the sections below to build today's care plan.")

    # ------------------------------------------------------------------
    # Section B — Pets
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("2. Your Pets")

    with st.form("pet_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pet_name = st.text_input("Name", value="Buddy")
        with col2:
            pet_breed = st.text_input("Breed", value="Labrador")
        with col3:
            pet_type = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
        with col4:
            pet_priority = st.number_input("Priority (1 = highest)", min_value=1, max_value=10, value=1)

        if st.form_submit_button("Add pet"):
            if pet_name in [p.name for p in owner.pets]:
                st.warning(f"A pet named **{pet_name}** already exists.")
            else:
                owner.add_pet(Pet(name=pet_name, breed=pet_breed, type=pet_type, priority=int(pet_priority)))
                st.success(f"**{pet_name}** added!")

    if owner.pets:
        st.dataframe(
            [{"Name": p.name, "Breed": p.breed, "Species": p.type, "Priority": p.priority}
             for p in owner.get_pets_by_priority()],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No pets yet — add one above.")

    # ------------------------------------------------------------------
    # Section C — Tasks
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("3. Care Tasks")

    if not owner.pets:
        st.info("Add a pet first.")
    else:
        with st.form("task_form"):
            col1, col2 = st.columns(2)
            with col1:
                target_pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
                task_type       = st.selectbox("Task type", [t.value for t in TaskType])
                task_desc       = st.text_input("Description", value="Morning walk")
            with col2:
                task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
                task_priority = st.selectbox("Priority", ["high", "medium", "low"])
                task_freq     = st.selectbox("Frequency", [f.value for f in Frequency])

            if st.form_submit_button("Add task"):
                owner.get_pet(target_pet_name).add_task(Task(
                    task_type=TaskType(task_type),
                    description=task_desc,
                    duration_minutes=int(task_duration),
                    priority=task_priority,
                    frequency=Frequency(task_freq),
                ))
                st.success(f"**{task_type}** added to {target_pet_name}.")

        # Task summary per pet — collapsed by default to save space
        for pet in owner.pets:
            if pet.tasks:
                with st.expander(f"{pet.name}'s tasks ({len(pet.tasks)} total, "
                                 f"{len(pet.get_pending_tasks())} pending)"):
                    st.dataframe(
                        [{"Type": t.task_type.value,
                          "Description": t.description,
                          "Duration (min)": t.duration_minutes,
                          "Priority": t.priority,
                          "Frequency": t.frequency.value,
                          "Done": "✔" if t.is_completed else "—"}
                         for t in pet.tasks],
                        use_container_width=True,
                        hide_index=True,
                    )

    # ------------------------------------------------------------------
    # Section D — Time slots
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("4. Your Free Time Today")

    with st.form("slot_form"):
        col1, col2 = st.columns(2)
        with col1:
            start = st.text_input("Start (HH:MM)", value="08:00")
        with col2:
            end = st.text_input("End   (HH:MM)", value="08:30")

        if st.form_submit_button("Add time slot"):
            try:
                slot = TimeSlot(start_time=start, end_time=end)
                _ = slot.duration_minutes   # validate by triggering the property
                owner.add_time_slot(slot)
                st.success(f"Slot **{start}–{end}** added ({slot.duration_minutes} min).")
            except Exception:
                st.error("Invalid format — use HH:MM (e.g. 08:00).")

    if owner.available_time:
        total_free = sum(s.duration_minutes for s in owner.get_free_slots())
        st.caption(f"Total free time: **{total_free} minutes**")
        st.dataframe(
            [{"Start": s.start_time, "End": s.end_time,
              "Duration (min)": s.duration_minutes,
              "Status": "Free" if s.is_available() else f"Blocked — {s.occupied_by}"}
             for s in owner.available_time],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No time slots yet — add some above.")

    # ------------------------------------------------------------------
    # Section E — Generate & display schedule
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("5. Today's Care Plan")

    schedule_date = st.date_input("Plan for date").strftime("%Y-%m-%d")

    if st.button("Generate schedule", type="primary"):
        if not owner.pets:
            st.warning("Add at least one pet first.")
        elif not any(pet.tasks for pet in owner.pets):
            st.warning("Add at least one task to a pet first.")
        elif not owner.available_time:
            st.warning("Add at least one free time slot first.")
        else:
            scheduler = Scheduler(owner=owner)
            plan = scheduler.generate_daily_plan(date=schedule_date)
            st.session_state.last_plan = plan
            st.session_state.last_scheduler = scheduler

    # Display is driven by session_state so it persists across reruns
    plan      = st.session_state.last_plan
    scheduler = st.session_state.last_scheduler

    if plan is not None:

        # ── Conflict warnings ─────────────────────────────────────
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.error("**Scheduling conflicts detected** — two or more tasks overlap in time. "
                     "Consider shortening a task or adding more free slots.")
            for msg in conflicts:
                # Strip the leading emoji/label and surface it as a clear banner
                parts = msg.replace("⚠  CONFLICT: ", "").split(" overlaps ")
                if len(parts) == 2:
                    st.warning(f"**{parts[0]}**  overlaps with  **{parts[1]}**")
                else:
                    st.warning(msg)

        # ── Scheduled tasks (sorted chronologically) ──────────────
        sorted_tasks = scheduler.sort_by_time()
        if sorted_tasks:
            st.success(f"**{len(sorted_tasks)} task(s) scheduled** for {plan.date} — "
                       f"shown in chronological order.")
            st.dataframe(
                [{"Time": f"{e.time_slot.start_time}–{e.time_slot.end_time}",
                  "Pet": e.pet.name,
                  "Task": e.task.task_type.value.capitalize(),
                  "Description": e.task.description,
                  "Duration": f"{e.task.duration_minutes} min",
                  "Why scheduled": e.reasoning}
                 for e in sorted_tasks],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No tasks could be scheduled. Try adding more free time slots.")

        # ── Unscheduled tasks ──────────────────────────────────────
        if plan.unscheduled_tasks:
            st.warning(
                f"**{len(plan.unscheduled_tasks)} task(s) could not be scheduled** — "
                "no available slot was long enough. "
                "Add more free time or shorten the tasks below."
            )
            st.dataframe(
                [{"Pet": pet.name,
                  "Task": task.task_type.value.capitalize(),
                  "Description": task.description,
                  "Needs (min)": task.duration_minutes,
                  "Priority": task.priority}
                 for pet, task in plan.unscheduled_tasks],
                use_container_width=True,
                hide_index=True,
            )

        # ── Pending tasks (filter view) ────────────────────────────
        still_pending = scheduler.filter_tasks(completed=False)
        if still_pending:
            with st.expander(f"Still pending after this plan ({len(still_pending)} task(s))"):
                st.dataframe(
                    [{"Pet": pet.name,
                      "Task": task.task_type.value.capitalize(),
                      "Description": task.description,
                      "Priority": task.priority,
                      "Frequency": task.frequency.value}
                     for pet, task in still_pending],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.success("All tasks are accounted for — nothing left pending!")
