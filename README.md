# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond the basic daily plan, PawPal+ includes three algorithmic extensions:

### Task Filtering
`Scheduler.filter_tasks(completed, pet_name)` searches across all pets' task lists
directly, so you can query completed or pending tasks even after the scheduler has run.
Both parameters are optional and can be combined.

```python
scheduler.filter_tasks(completed=False, pet_name="Buddy")  # Buddy's pending tasks
scheduler.filter_tasks(completed=True)                      # all done tasks, any pet
```

### Recurring Tasks
`CareTask` accepts a `recurrence` field (`"daily"` or `"weekly"`) and a `due_date`.
When `Scheduler.complete_task(task)` is called on a recurring task it automatically:
- marks the current instance complete
- creates a fresh copy with `due_date` advanced by 1 or 7 days
- appends the new copy to the same pet's task list
- logs the action in the reasoning log

One-off tasks (no `recurrence`) behave as before — `complete_task` returns `None`.

### Conflict Detection
`Scheduler.detect_conflicts()` performs a pairwise scan of `scheduled_entries` using
the standard interval-overlap test (`a.start < b.end AND b.start < a.end`). It returns
a list of `ScheduleConflict` objects, each recording the two entries, the overlap in
minutes, and whether they belong to the same pet or different pets.

`send_plan()` calls this automatically and prints a prominent
`[!] SCHEDULE CONFLICTS DETECTED` banner at the top of the output if any overlaps are
found. The normal `build_schedule` path always produces zero conflicts; the check acts
as a validation guard for any external modifications to `scheduled_entries`.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
