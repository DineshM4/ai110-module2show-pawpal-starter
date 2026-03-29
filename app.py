import streamlit as st
from pawpal_system import Owner, Pet, CareTask, Scheduler
from datetime import date

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# --- Session initialization (runs only once per browser session) ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        available_times=["07:00-08:00", "12:00-13:00", "18:00-19:00"]
    )

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(
        owner=st.session_state.owner,
        date=date.today().strftime("%Y-%m-%d")
    )

owner = st.session_state.owner
scheduler = st.session_state.scheduler

# ------------------------------------------------------------------ #
# Owner Setup
# ------------------------------------------------------------------ #
st.subheader("Owner Setup")

owner_name_input = st.text_input("Owner name", value=owner.name)
availability_input = st.text_input(
    "Available time slots (comma-separated, e.g. 07:00-08:00, 12:00-13:00)",
    value=", ".join(owner.available_times),
)

if st.button("Update owner"):
    owner.name = owner_name_input
    owner.update_availability(
        [s.strip() for s in availability_input.split(",") if s.strip()]
    )
    st.success(f"Owner updated: {owner.name} — slots: {owner.available_times}")

st.divider()

# ------------------------------------------------------------------ #
# Add a Pet
# ------------------------------------------------------------------ #
st.subheader("Add a Pet")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Buddy")
with col2:
    species = st.selectbox("Species", ["Dog", "Cat", "Other"])
with col3:
    breed = st.text_input("Breed", value="")

if st.button("Add pet"):
    new_pet = Pet(name=pet_name, species=species, breed=breed)
    owner.add_pet(new_pet)
    st.success(f"Added {pet_name} ({species}) to {owner.name}'s roster.")

if owner.pets:
    st.write("Current pets:")
    st.table([
        {"Name": p.name, "Species": p.species, "Breed": p.breed or "—"}
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ------------------------------------------------------------------ #
# Add a Care Task
# ------------------------------------------------------------------ #
st.subheader("Add a Care Task")

PRIORITY_MAP = {"Critical": 1, "Important": 2, "Optional": 3}

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    selected_pet_name = st.selectbox(
        "Assign to pet", [p.name for p in owner.pets])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        task_name = st.text_input("Task name", value="Morning Walk")
    with col2:
        category = st.selectbox(
            "Category", ["Exercise", "Feeding",
                         "Grooming", "Medical", "Enrichment"]
        )
    with col3:
        duration = st.number_input(
            "Duration (min)", min_value=1, max_value=240, value=30)
    with col4:
        priority_label = st.selectbox("Priority", list(PRIORITY_MAP.keys()))
    with col5:
        recurrence_label = st.selectbox("Recurrence", ["None", "daily", "weekly"])

    if st.button("Add task"):
        target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
        recurrence = None if recurrence_label == "None" else recurrence_label
        task = CareTask(
            name=task_name,
            category=category,
            duration=int(duration),
            priority=PRIORITY_MAP[priority_label],
            recurrence=recurrence,
            due_date=date.today().strftime("%Y-%m-%d") if recurrence else "",
        )
        target_pet.add_task(task)
        st.success(f"Added '{task_name}' to {selected_pet_name}.")

    all_tasks = [
        {
            "Pet": p.name,
            "Task": t.name,
            "Category": t.category,
            "Duration (min)": t.duration,
            "Priority": t.priority,
            "Recurrence": t.recurrence or "—",
            "Status": "Done" if t.completed else "Pending",
        }
        for p in owner.pets
        for t in p.tasks
    ]
    if all_tasks:
        st.write("Current tasks:")
        st.table(all_tasks)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ------------------------------------------------------------------ #
# Mark Task Complete
# ------------------------------------------------------------------ #
st.subheader("Mark Task Complete")

incomplete_tasks = [
    (p, t) for p in owner.pets for t in p.tasks if not t.completed
]

if not owner.pets:
    st.info("Add a pet first before completing tasks.")
elif not incomplete_tasks:
    st.info("No incomplete tasks. All done, or add tasks above.")
else:
    task_options = {
        f"{p.name} — {t.name} ({t.category}, {t.duration} min"
        + (f", {t.recurrence}" if t.recurrence else "")
        + ")": (p, t)
        for p, t in incomplete_tasks
    }
    selected_label = st.selectbox("Select task to complete", list(task_options.keys()))
    _, selected_task = task_options[selected_label]

    if st.button("Mark complete"):
        next_task = scheduler.complete_task(selected_task)
        st.success(f"'{selected_task.name}' marked complete for {selected_task.pet_name}.")
        if next_task:
            st.info(
                f"Recurring ({selected_task.recurrence}) — next occurrence of "
                f"**'{next_task.name}'** queued for **{next_task.due_date}**."
            )

    # Live task status table
    status_rows = [
        {
            "Pet": p.name,
            "Task": t.name,
            "Recurrence": t.recurrence or "—",
            "Due": t.due_date or "—",
            "Status": "Done" if t.completed else "Pending",
        }
        for p in owner.pets
        for t in p.tasks
    ]
    st.table(status_rows)

st.divider()

# ------------------------------------------------------------------ #
# Generate Schedule
# ------------------------------------------------------------------ #
st.subheader("Build Schedule")

buffer_minutes = st.slider(
    "Buffer between tasks (min)", min_value=0, max_value=15, value=5)

PRIORITY_LABEL = {1: "Critical", 2: "Important", 3: "Optional"}

if st.button("Generate schedule"):
    if not owner.pets or not any(p.tasks for p in owner.pets):
        st.warning(
            "Add at least one pet with tasks before generating a schedule.")
    elif not owner.available_times:
        st.warning(
            "Set the owner's available time slots before generating a schedule.")
    else:
        scheduler.buffer_minutes = buffer_minutes
        scheduler.build_schedule()

        total = len(scheduler.scheduled_entries) + \
            len(scheduler.unscheduled_tasks)
        n_scheduled = len(scheduler.scheduled_entries)
        st.success(
            f"Schedule built for **{scheduler.date}** — "
            f"{n_scheduled}/{total} tasks placed."
        )

        # ── Conflict warnings ──────────────────────────────────────
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.markdown("#### ⚠️ Schedule Conflicts Detected")
            for c in conflicts:
                a, b = c.entry_a, c.entry_b
                scope = "same pet" if c.same_pet else "different pets"
                a_end = f"{a.end_minutes // 60:02d}:{a.end_minutes % 60:02d}"
                b_end = f"{b.end_minutes // 60:02d}:{b.end_minutes % 60:02d}"
                st.warning(
                    f"**{c.overlap_minutes}-min overlap** ({scope})  \n"
                    f"- **{a.task.name}** ({a.task.pet_name}): "
                    f"{a.scheduled_time} – {a_end}  \n"
                    f"- **{b.task.name}** ({b.task.pet_name}): "
                    f"{b.scheduled_time} – {b_end}  \n"
                    f"_Tip: adjust the duration or time slot of one of these tasks "
                    f"to eliminate the overlap._"
                )

        # ── Critical tasks that couldn't be scheduled ──────────────
        critical_unscheduled = [
            t for t in scheduler.unscheduled_tasks if t.priority == 1
        ]
        if critical_unscheduled:
            st.markdown("#### 🚨 Critical Tasks Could Not Be Scheduled")
            for t in critical_unscheduled:
                st.error(
                    f"**{t.name}** ({t.pet_name}) needs **{t.duration} min** — "
                    f"no available slot is long enough.  \n"
                    f"_Extend your availability or shorten other tasks to fit this critical task._"
                )

        # ── Time-window blocks ─────────────────────────────────────
        st.markdown("#### 📅 Daily Schedule")
        slots = owner.parse_time_slots()

        for (start, end), raw in zip(slots, owner.available_times):
            label = Scheduler._window_label(start)
            total_min = end - start

            window_entries = sorted(
                [e for e in scheduler.scheduled_entries
                 if start <= e.start_minutes < end],
                key=lambda e: e.start_minutes,
            )
            used_min = sum(e.task.duration for e in window_entries)
            pct = int(used_min / total_min * 100) if total_min else 0

            with st.expander(
                f"**{label}**  •  {raw}  —  {used_min}/{total_min} min used ({pct}%)",
                expanded=True,
            ):
                if window_entries:
                    st.table([
                        {
                            "Time": e.scheduled_time,
                            "Task": e.task.name,
                            "Pet": e.task.pet_name,
                            "Duration": f"{e.task.duration} min",
                            "Category": e.task.category,
                            "Priority": PRIORITY_LABEL[e.task.priority],
                        }
                        for e in window_entries
                    ])
                else:
                    st.info("No tasks scheduled in this window.")

        # ── Non-critical unscheduled tasks ─────────────────────────
        non_critical_unscheduled = [
            t for t in scheduler.unscheduled_tasks if t.priority != 1
        ]
        if non_critical_unscheduled:
            st.markdown("#### ❌ Could Not Schedule")
            best_raw, best_free = (
                max(scheduler._slot_free_after_build, key=lambda x: x[1])
                if scheduler._slot_free_after_build
                else ("", 0)
            )
            for t in non_critical_unscheduled:
                needed = t.duration - best_free
                tip = (
                    f"Extend your **{best_raw}** slot by ~{needed} min to fit this task."
                    if needed > 0
                    else "Re-run after marking other tasks complete to free up slot time."
                )
                st.warning(
                    f"**{t.name}** ({t.pet_name}) — needs {t.duration} min  \n_{tip}_"
                )

        # ── Per-pet progress ───────────────────────────────────────
        pets_with_tasks = [p for p in owner.pets if p.tasks]
        if pets_with_tasks:
            st.markdown("#### 🐾 Pet Progress")
            cols = st.columns(len(pets_with_tasks))
            for col, pet in zip(cols, pets_with_tasks):
                done = sum(1 for t in pet.tasks if t.completed)
                total_pet = len(pet.tasks)
                pct = int(done / total_pet * 100)
                col.metric(
                    label=f"{pet.name} ({pet.species})",
                    value=f"{done}/{total_pet} tasks",
                    delta=f"{pct}% complete",
                )

        # ── Scheduling reasoning log ───────────────────────────────
        if scheduler.reasoning_log:
            with st.expander("Scheduling Reasoning Log", expanded=False):
                for reason in scheduler.reasoning_log:
                    st.write(f"• {reason}")
