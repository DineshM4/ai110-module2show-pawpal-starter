from pawpal_system import CareTask, Pet, Owner, Scheduler, ScheduledEntry
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_task():
    return CareTask(name="Bath", category="Grooming", duration=30, priority=2)


@pytest.fixture
def sample_pet():
    return Pet(name="Buddy", species="Dog")


@pytest.fixture
def scheduler_with_pet():
    owner = Owner(name="Alice", available_times=["08:00-10:00"])
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, date="2026-03-29")
    return scheduler, pet


def test_mark_complete_changes_status(sample_task):
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_add_task_increases_pet_task_count(sample_pet, sample_task):
    assert len(sample_pet.tasks) == 0
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == 1


# --- Edge Case 1: Completing the same task twice creates a duplicate recurring task ---

def test_completing_recurring_task_twice_adds_duplicate(scheduler_with_pet):
    scheduler, pet = scheduler_with_pet
    task = CareTask(name="Feed", category="Feeding", duration=10, priority=1,
                    recurrence="daily", due_date="2026-03-29")
    pet.add_task(task)

    scheduler.complete_task(task)
    assert len(pet.tasks) == 2  # original + one next occurrence

    # Completing an already-completed task again adds a second duplicate
    scheduler.complete_task(task)
    assert len(pet.tasks) == 3  # demonstrates the bug: two next occurrences queued


# --- Edge Case 2: complete_task raises ValueError for an orphaned task ---

def test_complete_task_raises_for_orphaned_task(scheduler_with_pet):
    scheduler, pet = scheduler_with_pet
    orphan = CareTask(name="Mystery Walk", category="Exercise", duration=20, priority=2)
    # orphan is never added to any pet

    with pytest.raises(ValueError, match="Mystery Walk"):
        scheduler.complete_task(orphan)


# --- Edge Case 3: Adjacent tasks (touching, not overlapping) are not flagged as conflicts ---

def test_adjacent_tasks_are_not_a_conflict(scheduler_with_pet):
    scheduler, pet = scheduler_with_pet
    task_a = CareTask(name="Feed", category="Feeding", duration=30, priority=1, pet_name="Buddy")
    task_b = CareTask(name="Walk", category="Exercise", duration=30, priority=2, pet_name="Buddy")

    # entry_a: 08:00–08:30, entry_b starts exactly at 08:30 (adjacent, not overlapping)
    entry_a = ScheduledEntry(task=task_a, scheduled_time="08:00")
    entry_b = ScheduledEntry(task=task_b, scheduled_time="08:30")
    scheduler.scheduled_entries = [entry_a, entry_b]

    conflicts = scheduler.detect_conflicts()
    assert conflicts == [], "Adjacent tasks must not be reported as a conflict"


# --- Edge Case 4: Overlapping availability windows double-count available minutes ---

def test_overlapping_availability_windows_double_count_minutes():
    # Two windows that share 08:00–09:00 — parse_time_slots does not merge them
    owner = Owner(name="Bob", available_times=["07:00-09:00", "08:00-10:00"])
    slots = owner.parse_time_slots()

    # There are two separate tuples, so 08:00–09:00 is represented twice
    assert len(slots) == 2
    starts = [s for s, _ in slots]
    assert 7 * 60 in starts and 8 * 60 in starts  # both windows parsed independently


# --- Edge Case 5: recurrence="" (empty string) is treated as non-recurring ---

def test_empty_string_recurrence_returns_none():
    task = CareTask(name="Groom", category="Grooming", duration=20, priority=3,
                    recurrence="")  # empty string instead of None

    result = task.next_occurrence()
    assert result is None, "Empty-string recurrence should be treated as non-recurring"


# --- Sorting Correctness: scheduled_entries are in chronological order after build_schedule ---

def test_build_schedule_entries_are_chronological():
    # Three tasks added in reverse priority order; higher priority must land at earlier times.
    # A single slot forces all tasks into one sequential sequence, so scheduled_entries
    # must be sorted by start_minutes after build_schedule().
    owner = Owner(name="Alice", available_times=["08:00-12:00"])
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)

    low  = CareTask(name="Optional Groom", category="Grooming",  duration=20, priority=3)
    mid  = CareTask(name="Important Walk", category="Exercise",  duration=20, priority=2)
    high = CareTask(name="Critical Meds",  category="Medical",   duration=20, priority=1)

    # Add in reverse priority order to confirm sorting isn't relying on insertion order
    pet.add_task(low)
    pet.add_task(mid)
    pet.add_task(high)

    scheduler = Scheduler(owner=owner, date="2026-03-29")
    scheduler.build_schedule()

    assert len(scheduler.scheduled_entries) == 3, "All three tasks should be scheduled"

    times = [e.start_minutes for e in scheduler.scheduled_entries]
    assert times == sorted(times), "scheduled_entries must be in ascending time order"

    # The highest-priority task (Critical Meds, priority=1) must occupy the earliest slot
    first_entry = scheduler.scheduled_entries[0]
    assert first_entry.task.name == "Critical Meds", (
        "Priority-1 task must be placed first (earliest start time)"
    )


# --- Conflict Detection: two tasks at the exact same time are flagged as a conflict ---

def test_detect_conflicts_flags_duplicate_start_times(scheduler_with_pet):
    scheduler, pet = scheduler_with_pet

    task_a = CareTask(name="Feed",  category="Feeding",  duration=30, priority=1, pet_name="Buddy")
    task_b = CareTask(name="Brush", category="Grooming", duration=20, priority=2, pet_name="Buddy")

    # Both entries start at 08:00 — a direct time collision on the same pet
    entry_a = ScheduledEntry(task=task_a, scheduled_time="08:00")
    entry_b = ScheduledEntry(task=task_b, scheduled_time="08:00")
    scheduler.scheduled_entries = [entry_a, entry_b]

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1, "Exactly one conflict should be detected"
    conflict = conflicts[0]
    assert conflict.same_pet is True, "Both tasks belong to Buddy — same_pet must be True"
    # Overlap equals the shorter task's full duration (task_b = 20 min fits inside task_a = 30 min)
    assert conflict.overlap_minutes == 20
