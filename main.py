from pawpal_system import CareTask, Pet, Owner, Scheduler, ScheduledEntry
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

today = date.today().strftime("%Y-%m-%d")

# --- Add Tasks OUT OF ORDER (mixed priorities across pets) ---
buddy.add_task(CareTask(name="Bath",            category="Grooming",   duration=25, priority=3))  # low priority first
buddy.add_task(CareTask(name="Morning Walk",    category="Exercise",   duration=30, priority=1, recurrence="daily",  due_date=today))
buddy.add_task(CareTask(name="Vet Checkup",     category="Medical",    duration=20, priority=1))  # one-off
buddy.add_task(CareTask(name="Breakfast",       category="Feeding",    duration=10, priority=1, recurrence="daily",  due_date=today))

whiskers.add_task(CareTask(name="Playtime",     category="Enrichment", duration=20, priority=2, recurrence="weekly", due_date=today))
whiskers.add_task(CareTask(name="Brush Coat",   category="Grooming",   duration=15, priority=2))  # one-off
whiskers.add_task(CareTask(name="Breakfast",    category="Feeding",    duration=10, priority=1, recurrence="daily",  due_date=today))

# --- Build Schedule ---
scheduler = Scheduler(owner=owner, date=today)
scheduler.build_schedule()

# --- Print full schedule (shows sorting by priority applied internally) ---
print(scheduler.send_plan())

# --- Demonstrate filter_tasks ---
SEP = "-" * 52

print(f"\n{SEP}")
print("FILTER: all incomplete tasks (any pet)")
print(SEP)
incomplete = scheduler.filter_tasks(completed=False)
for t in incomplete:
    print(f"  [{t.priority}] {t.name:<20} {t.pet_name:<12} {t.category}")

print(f"\n{SEP}")
print("FILTER: Buddy's tasks only")
print(SEP)
buddy_tasks = scheduler.filter_tasks(pet_name="Buddy")
for t in buddy_tasks:
    status = "done" if t.completed else "pending"
    print(f"  [{t.priority}] {t.name:<20} {t.duration} min  [{status}]")

print(f"\n{SEP}")
print("FILTER: Whiskers's tasks only")
print(SEP)
whiskers_tasks = scheduler.filter_tasks(pet_name="Whiskers")
for t in whiskers_tasks:
    status = "done" if t.completed else "pending"
    print(f"  [{t.priority}] {t.name:<20} {t.duration} min  [{status}]")

# --- Demonstrate recurrence via complete_task ---
print(f"\n{SEP}")
print("RECURRENCE: completing recurring tasks")
print(SEP)

recurring_demos = [
    (buddy,    buddy.tasks[1],    "Morning Walk (daily)"),
    (buddy,    buddy.tasks[3],    "Breakfast — Buddy (daily)"),
    (whiskers, whiskers.tasks[0], "Playtime — Whiskers (weekly)"),
    (buddy,    buddy.tasks[2],    "Vet Checkup (one-off, no recurrence)"),
]

for pet, task, label in recurring_demos:
    next_t = scheduler.complete_task(task)
    if next_t:
        print(f"  Completed '{label}' → next occurrence due {next_t.due_date} ({next_t.recurrence})")
    else:
        print(f"  Completed '{label}' → no recurrence (one-off)")

print(f"\n  Buddy now has {len(buddy.tasks)} tasks (was 4 before completions)")
print(f"  Whiskers now has {len(whiskers.tasks)} tasks (was 3 before completions)")

print(f"\n{SEP}")
print("FILTER: all tasks for Buddy (including next occurrences)")
print(SEP)
for t in scheduler.filter_tasks(pet_name="Buddy"):
    status = "done" if t.completed else "pending"
    recur  = f" [{t.recurrence}]" if t.recurrence else ""
    due    = f" due {t.due_date}" if t.due_date else ""
    print(f"  [{t.priority}] {t.name:<20}{due}{recur}  [{status}]")

print(f"\n{SEP}")
print("FILTER: completed tasks after recurrence completions")
print(SEP)
for t in scheduler.filter_tasks(completed=True):
    print(f"  {t.name:<20} {t.pet_name:<12} due {t.due_date}")

print(f"\n{SEP}")
print("FILTER: Buddy's incomplete tasks only")
print(SEP)
for t in scheduler.filter_tasks(completed=False, pet_name="Buddy"):
    due = f" due {t.due_date}" if t.due_date else ""
    print(f"  [{t.priority}] {t.name:<20}{due}  {t.duration} min")

# --- Conflict detection demo ---
# Rebuild a clean schedule, then manually inject two overlapping entries
# to simulate what would happen if tasks were force-assigned the same slot.
print(f"\n{SEP}")
print("CONFLICT DETECTION: injecting overlapping tasks")
print(SEP)

scheduler2 = Scheduler(owner=owner, date=today)
scheduler2.build_schedule()

# Grab the first scheduled slot's start time so both injected tasks land there
first_entry = scheduler2.scheduled_entries[0]
overlap_time = first_entry.scheduled_time

# Same-pet conflict: two of Buddy's tasks at the identical start time
clash_a = ScheduledEntry(
    task=CareTask(name="Extra Walk",  category="Exercise", duration=20, priority=2, pet_name="Buddy"),
    scheduled_time=overlap_time,
)
# Cross-pet conflict: a Whiskers task that also starts at the same time
clash_b = ScheduledEntry(
    task=CareTask(name="Vet Visit",   category="Medical",  duration=30, priority=1, pet_name="Whiskers"),
    scheduled_time=overlap_time,
)

scheduler2.scheduled_entries.extend([clash_a, clash_b])

# detect_conflicts() surfaces the problem
conflicts = scheduler2.detect_conflicts()
print(f"  {len(conflicts)} conflict(s) found after injection:\n")
for c in conflicts:
    print(f"  {c}")

# send_plan() now prints the CONFLICTS DETECTED banner at the top
print()
print(scheduler2.send_plan())
