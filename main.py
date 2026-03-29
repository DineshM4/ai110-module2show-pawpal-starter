from pawpal_system import CareTask, Pet, Owner, Scheduler
from datetime import date

# --- Setup Owner ---
owner = Owner(
    name="Jordan",
    available_times=["07:00-08:00", "12:00-13:00", "18:00-19:00"]
)

# --- Setup Pets ---
buddy = Pet(name="Buddy", species="Dog", breed="Golden Retriever")
whiskers = Pet(name="Whiskers", species="Cat", breed="Tabby")

owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Add Tasks to Buddy (Dog) ---
buddy.add_task(CareTask(name="Morning Walk",    category="Exercise",  duration=30, priority=1))
buddy.add_task(CareTask(name="Breakfast",       category="Feeding",   duration=10, priority=1))
buddy.add_task(CareTask(name="Bath",            category="Grooming",  duration=25, priority=3))

# --- Add Tasks to Whiskers (Cat) ---
whiskers.add_task(CareTask(name="Breakfast",    category="Feeding",   duration=10, priority=1))
whiskers.add_task(CareTask(name="Brush Coat",   category="Grooming",  duration=15, priority=2))
whiskers.add_task(CareTask(name="Playtime",     category="Enrichment",duration=20, priority=2))

# --- Build and Print Schedule ---
today = date.today().strftime("%Y-%m-%d")
scheduler = Scheduler(owner=owner, date=today)
scheduler.build_schedule()

print(scheduler.send_plan())
