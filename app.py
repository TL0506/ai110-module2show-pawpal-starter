import streamlit as st

# Step 1 — import the logic layer
from pawpal_system import (
    Owner, Pet, Task, TaskType, Frequency, TimeSlot, Scheduler
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ------------------------------------------------------------------
# Step 2 — session_state vault
# Streamlit reruns top-to-bottom on every interaction, so the Owner
# object lives in session_state rather than being recreated each run.
# ------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ------------------------------------------------------------------
# Section A — Owner setup (always visible)
# ------------------------------------------------------------------
st.subheader("1. Owner Setup")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    submitted = st.form_submit_button("Set owner")
    if submitted:
        if st.session_state.owner is None:
            st.session_state.owner = Owner(name=owner_name)
        else:
            st.session_state.owner.name = owner_name

if st.session_state.owner is None:
    st.info("Submit your name above to get started.")

# ------------------------------------------------------------------
# Everything below only renders once an Owner exists.
# Using an explicit if-block instead of st.stop() because st.stop()
# is unreliable across Streamlit rerun contexts.
# ------------------------------------------------------------------
if st.session_state.owner is not None:
    owner: Owner = st.session_state.owner
    st.success(f"Owner: **{owner.name}**")

    # ------------------------------------------------------------------
    # Section B — Add a pet
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("2. Add a Pet")

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

        add_pet = st.form_submit_button("Add pet")
        if add_pet:
            existing_names = [p.name for p in owner.pets]
            if pet_name in existing_names:
                st.warning(f"A pet named **{pet_name}** already exists.")
            else:
                owner.add_pet(Pet(name=pet_name, breed=pet_breed, type=pet_type, priority=int(pet_priority)))
                st.success(f"Added **{pet_name}**!")

    if owner.pets:
        st.write("**Current pets:**")
        st.table([
            {"Name": p.name, "Breed": p.breed, "Species": p.type, "Priority": p.priority}
            for p in owner.get_pets_by_priority()
        ])
    else:
        st.info("No pets yet — add one above.")

    # ------------------------------------------------------------------
    # Section C — Add tasks to a pet
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("3. Add a Task to a Pet")

    if not owner.pets:
        st.info("Add a pet first.")
    else:
        with st.form("task_form"):
            target_pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
            col1, col2 = st.columns(2)
            with col1:
                task_type = st.selectbox("Task type", [t.value for t in TaskType])
                task_desc = st.text_input("Description", value="Morning walk")
                task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            with col2:
                task_priority = st.selectbox("Priority", ["high", "medium", "low"])
                task_freq = st.selectbox("Frequency", [f.value for f in Frequency])

            add_task = st.form_submit_button("Add task")
            if add_task:
                target_pet = owner.get_pet(target_pet_name)
                new_task = Task(
                    task_type=TaskType(task_type),
                    description=task_desc,
                    duration_minutes=int(task_duration),
                    priority=task_priority,
                    frequency=Frequency(task_freq),
                )
                target_pet.add_task(new_task)
                st.success(f"Added **{task_type}** to {target_pet_name}.")

        for pet in owner.pets:
            if pet.tasks:
                st.write(f"**{pet.name}'s tasks:**")
                st.table([
                    {
                        "Type": t.task_type.value,
                        "Description": t.description,
                        "Duration (min)": t.duration_minutes,
                        "Priority": t.priority,
                        "Frequency": t.frequency.value,
                    }
                    for t in pet.tasks
                ])

    # ------------------------------------------------------------------
    # Section D — Owner availability (time slots)
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("4. Add a Free Time Slot")

    with st.form("slot_form"):
        col1, col2 = st.columns(2)
        with col1:
            start = st.text_input("Start time (HH:MM)", value="08:00")
        with col2:
            end = st.text_input("End time   (HH:MM)", value="08:30")

        add_slot = st.form_submit_button("Add slot")
        if add_slot:
            try:
                owner.add_time_slot(TimeSlot(start_time=start, end_time=end))
                st.success(f"Slot {start}–{end} added.")
            except Exception:
                st.error("Invalid time format. Use HH:MM (e.g. 08:00).")

    if owner.available_time:
        st.write("**Available slots:**")
        st.table([
            {"Start": s.start_time, "End": s.end_time, "Duration (min)": s.duration_minutes}
            for s in owner.available_time
        ])
    else:
        st.info("No time slots yet — add one above.")

    # ------------------------------------------------------------------
    # Section E — Generate schedule
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("5. Generate Today's Schedule")

    schedule_date = st.date_input("Date").strftime("%Y-%m-%d")

    if st.button("Generate schedule"):
        if not owner.pets:
            st.warning("Add at least one pet first.")
        elif not any(pet.tasks for pet in owner.pets):
            st.warning("Add at least one task to a pet first.")
        elif not owner.available_time:
            st.warning("Add at least one free time slot first.")
        else:
            scheduler = Scheduler(owner=owner)
            plan = scheduler.generate_daily_plan(date=schedule_date)

            st.success("Schedule generated!")

            if plan.scheduled_tasks:
                st.write("**Scheduled tasks:**")
                st.table([
                    {
                        "Time": f"{e.time_slot.start_time}–{e.time_slot.end_time}",
                        "Pet": e.pet.name,
                        "Task": e.task.task_type.value,
                        "Description": e.task.description,
                        "Why": e.reasoning,
                    }
                    for e in plan.scheduled_tasks
                ])

            if plan.unscheduled_tasks:
                st.warning("The following tasks could not fit into any available slot:")
                st.table([
                    {"Pet": pet.name, "Task": task.task_type.value, "Duration (min)": task.duration_minutes}
                    for pet, task in plan.unscheduled_tasks
                ])
