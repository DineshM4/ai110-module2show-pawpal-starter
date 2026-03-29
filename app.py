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

    col1, col2, col3, col4 = st.columns(4)
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

    if st.button("Add task"):
        target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
        task = CareTask(
            name=task_name,
            category=category,
            duration=int(duration),
            priority=PRIORITY_MAP[priority_label],
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
# Generate Schedule
# ------------------------------------------------------------------ #
st.subheader("Build Schedule")

buffer_minutes = st.slider(
    "Buffer between tasks (min)", min_value=0, max_value=15, value=5)

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
        st.code(scheduler.send_plan(), language=None)
