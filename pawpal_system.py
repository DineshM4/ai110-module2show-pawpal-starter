from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Tuple

# Improvement 2: category → preferred time-of-day windows
CATEGORY_PREFERENCES = {
    "Feeding":    ["Morning", "Evening"],
    "Exercise":   ["Morning", "Evening"],
    "Grooming":   ["Midday", "Afternoon"],
    "Medical":    ["Morning"],
    "Enrichment": ["Midday", "Afternoon", "Evening"],
}


@dataclass
class CareTask:
    name: str
    category: str  # e.g. "Grooming", "Feeding", "Medical"
    duration: int  # in minutes
    priority: int  # 1 = Critical, 2 = Important, 3 = Optional
    # set when task is added to a Pet; preserves identity after gather_all_tasks
    pet_name: str = ""
    completed: bool = False
    # Recurrence: None = one-off, "daily" = repeats every day, "weekly" = repeats every 7 days
    recurrence: Optional[str] = None
    # ISO date string (YYYY-MM-DD) of when this task is due; set automatically on recurrence
    due_date: str = ""

    def update_priority(self, priority: int) -> None:
        """Set the task's priority level (1=Critical, 2=Important, 3=Optional)."""
        self.priority = priority

    def update_duration(self, duration: int) -> None:
        """Update the estimated duration of the task in minutes."""
        self.duration = duration

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def next_occurrence(self) -> Optional["CareTask"]:
        """Return a new incomplete CareTask for the next recurrence, or None if not recurring.

        The new task's due_date is advanced by 1 day (daily) or 7 days (weekly)
        from this task's due_date, defaulting to today when due_date is unset.
        """
        if self.recurrence not in ("daily", "weekly"):
            return None
        delta = timedelta(days=1 if self.recurrence == "daily" else 7)
        base = date.fromisoformat(self.due_date) if self.due_date else date.today()
        next_due = (base + delta).isoformat()
        return CareTask(
            name=self.name,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            pet_name=self.pet_name,
            recurrence=self.recurrence,
            due_date=next_due,
        )


@dataclass
class ScheduledEntry:
    """Wraps a CareTask with a concrete time slot so the schedule records *when* each task runs."""
    task: CareTask
    scheduled_time: str  # e.g. "08:00"

    @property
    def start_minutes(self) -> int:
        """Scheduled start time in minutes since midnight."""
        h, m = map(int, self.scheduled_time.split(":"))
        return h * 60 + m

    @property
    def end_minutes(self) -> int:
        """Scheduled end time (exclusive) in minutes since midnight."""
        return self.start_minutes + self.task.duration


@dataclass
class ScheduleConflict:
    """Records a detected time overlap between two ScheduledEntries."""
    entry_a: ScheduledEntry
    entry_b: ScheduledEntry
    overlap_minutes: int
    same_pet: bool  # True when both tasks belong to the same pet

    def __str__(self) -> str:
        """Return a single-line human-readable conflict description.

        Format: CONFLICT (<scope>, <N> min overlap): '<task_a>' (<pet>) HH:MM–HH:MM × '<task_b>' (<pet>) HH:MM–HH:MM
        where <scope> is 'same pet' or 'different pets'.
        """
        a, b = self.entry_a, self.entry_b
        scope = "same pet" if self.same_pet else "different pets"
        return (
            f"CONFLICT ({scope}, {self.overlap_minutes} min overlap): "
            f"'{a.task.name}' ({a.task.pet_name}) {a.scheduled_time}–"
            f"{a.end_minutes // 60:02d}:{a.end_minutes % 60:02d}  ×  "
            f"'{b.task.name}' ({b.task.pet_name}) {b.scheduled_time}–"
            f"{b.end_minutes // 60:02d}:{b.end_minutes % 60:02d}"
        )


@dataclass
class Pet:
    name: str
    species: str
    breed: str = ""
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Assign a CareTask to this pet, stamping the pet's name onto the task."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: CareTask) -> None:
        """Remove an existing CareTask from this pet's task list."""
        self.tasks.remove(task)

    def update_breed_info(self, breed: str) -> None:
        """Update the pet's breed information."""
        self.breed = breed


class Owner:
    def __init__(self, name: str, available_times: List[str]):
        """Create an Owner with a name and a list of availability windows.

        Args:
            name:             The owner's display name.
            available_times:  List of 'HH:MM-HH:MM' strings defining free time blocks.
                              Parsed on first use and cached until update_availability() is called.
        """
        self.name = name
        # e.g. ["08:00-09:00", "17:00-18:00"]
        self.available_times = available_times
        self.pets: List[Pet] = []
        # Improvement 5: cache parsed slots; invalidated on update_availability()
        self._parsed_slots: Optional[List[Tuple[int, int]]] = None

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's roster."""
        self.pets.append(pet)

    def update_availability(self, times: List[str]) -> None:
        """Replace the owner's available time slots with a new list of 'HH:MM-HH:MM' strings."""
        self.available_times = times
        self._parsed_slots = None  # invalidate cache

    def parse_time_slots(self) -> List[Tuple[int, int]]:
        """Parse each 'HH:MM-HH:MM' availability string into a (start_minutes, end_minutes) tuple.
        Result is cached and only recomputed when availability changes."""
        if self._parsed_slots is None:
            slots = []
            for slot in self.available_times:
                start_str, end_str = slot.split("-")
                sh, sm = map(int, start_str.split(":"))
                eh, em = map(int, end_str.split(":"))
                slots.append((sh * 60 + sm, eh * 60 + em))
            self._parsed_slots = slots
        return self._parsed_slots


class Scheduler:
    def __init__(self, owner: Owner, date: str, buffer_minutes: int = 5):
        """Create a Scheduler for a single day's care plan.

        Args:
            owner:          The Owner whose pets and availability drive scheduling.
            date:           ISO date string (YYYY-MM-DD) displayed in the plan header.
            buffer_minutes: Gap inserted between consecutive tasks within a slot (default 5).
                            Prevents back-to-back tasks from running without any transition time.
        """
        self.owner = owner
        self.date = date
        # Improvement 3: configurable buffer between tasks (minutes)
        self.buffer_minutes = buffer_minutes
        self.all_tasks: List[CareTask] = []
        # replaces scheduled_tasks; carries time info
        self.scheduled_entries: List[ScheduledEntry] = []
        self.unscheduled_tasks: List[CareTask] = []
        self.reasoning_log: List[str] = []
        # Improvement 4: remaining free minutes per slot after last build
        self._slot_free_after_build: List[Tuple[str, int]] = []

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[CareTask]:
        """Return tasks across all pets filtered by completion status and/or pet name.

        Searches all pet tasks directly so completed tasks are visible even after
        gather_all_tasks (which skips them for scheduling purposes).

        Args:
            completed: If True, return only completed tasks; if False, only incomplete;
                       if None, no filter on completion status.
            pet_name:  If provided, return only tasks belonging to the named pet.
        """
        results: List[CareTask] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if completed is None or task.completed == completed:
                    results.append(task)
        return results

    def complete_task(self, task: CareTask) -> Optional[CareTask]:
        """Mark a task complete and, if it recurs, queue the next occurrence on the same pet.

        Returns the newly created CareTask for the next occurrence, or None for one-off tasks.
        Raises ValueError if the task is not found on any of the owner's pets.
        """
        # Locate the owning pet
        owner_pet: Optional[Pet] = None
        for pet in self.owner.pets:
            if task in pet.tasks:
                owner_pet = pet
                break
        if owner_pet is None:
            raise ValueError(f"Task '{task.name}' does not belong to any pet of {self.owner.name}")

        task.mark_complete()

        next_task = task.next_occurrence()
        if next_task is not None:
            owner_pet.add_task(next_task)
            self.reasoning_log.append(
                f"Recurring task '{task.name}' ({task.pet_name}) completed — "
                f"next {task.recurrence} occurrence queued for {next_task.due_date}"
            )
        return next_task

    def detect_conflicts(self) -> List[ScheduleConflict]:
        """Scan scheduled_entries for time overlaps and return every conflicting pair.

        Two entries conflict when their time ranges overlap:
            entry_a.start < entry_b.end  AND  entry_b.start < entry_a.end

        Works for both same-pet and cross-pet pairs. Returns an empty list when
        the schedule is conflict-free (the normal result after build_schedule).
        """
        conflicts: List[ScheduleConflict] = []
        entries = self.scheduled_entries
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                a, b = entries[i], entries[j]
                if a.start_minutes < b.end_minutes and b.start_minutes < a.end_minutes:
                    overlap = min(a.end_minutes, b.end_minutes) - max(a.start_minutes, b.start_minutes)
                    conflicts.append(ScheduleConflict(
                        entry_a=a,
                        entry_b=b,
                        overlap_minutes=overlap,
                        same_pet=(a.task.pet_name == b.task.pet_name),
                    ))
        return conflicts

    def gather_all_tasks(self) -> None:
        """Rebuild all_tasks by collecting every incomplete CareTask across all of the owner's pets."""
        self.all_tasks = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                # Improvement 6: skip already-completed tasks so re-runs don't re-schedule them
                if not task.completed:
                    task.pet_name = pet.name
                    self.all_tasks.append(task)

    def build_schedule(self) -> None:
        """Sort all tasks by priority then pet then duration, fit them into the owner's time slots, and log reasoning."""
        self.scheduled_entries = []
        self.unscheduled_tasks = []
        self.reasoning_log = []
        self._slot_free_after_build = []

        self.gather_all_tasks()

        # Improvement 1: sort by (priority, pet_name, duration) — groups same-pet tasks together
        sorted_tasks = sorted(
            self.all_tasks, key=lambda t: (t.priority, t.pet_name, t.duration)
        )

        # Each slot is a dict preserving original start for window-label lookups
        parsed = self.owner.parse_time_slots()
        slots = [
            {"raw": raw, "start": start, "cursor": start, "end": end}
            for raw, (start, end) in zip(self.owner.available_times, parsed)
        ]

        def _place(task: CareTask, candidates: List[dict]) -> Tuple[Optional[str], Optional[str]]:
            """Try to fit task into the first candidate slot with enough room.
            Returns (scheduled_time, window_label) on success, (None, None) otherwise."""
            for slot in candidates:
                if slot["end"] - slot["cursor"] >= task.duration:
                    t_str = f"{slot['cursor'] // 60:02d}:{slot['cursor'] % 60:02d}"
                    window = self._window_label(slot["start"])
                    self.scheduled_entries.append(
                        ScheduledEntry(task=task, scheduled_time=t_str))
                    # Improvement 3: advance cursor by task duration + buffer
                    slot["cursor"] += task.duration + self.buffer_minutes
                    return t_str, window
            return None, None

        for task in sorted_tasks:
            # Improvement 2: try preferred time windows first, fall back to any slot
            preferred_windows = CATEGORY_PREFERENCES.get(task.category)
            scheduled_time = None

            if preferred_windows:
                preferred_slots = [s for s in slots if self._window_label(
                    s["start"]) in preferred_windows]
                scheduled_time, window = _place(task, preferred_slots)
                if scheduled_time:
                    self.reasoning_log.append(
                        f"Scheduled '{task.name}' ({task.pet_name}) at {scheduled_time} "
                        f"[priority {task.priority}, {task.duration} min — preferred {window} window matched]"
                    )

            # Fall back to any slot if preferred windows had no room
            if not scheduled_time:
                scheduled_time, window = _place(task, slots)
                if scheduled_time:
                    self.reasoning_log.append(
                        f"Scheduled '{task.name}' ({task.pet_name}) at {scheduled_time} "
                        f"[priority {task.priority}, {task.duration} min]"
                    )

            if not scheduled_time:
                self.unscheduled_tasks.append(task)
                self.reasoning_log.append(
                    f"Could not schedule '{task.name}' ({task.pet_name}) "
                    f"[priority {task.priority}, {task.duration} min] — no available slot fits"
                )

        # Improvement 4: snapshot free space per slot for availability suggestions
        self._slot_free_after_build = [
            (s["raw"], max(0, s["end"] - s["cursor"])) for s in slots
        ]

    @staticmethod
    def _window_label(start_minutes: int) -> str:
        """Return a human-readable time-of-day label (Morning/Midday/Afternoon/Evening/Night) for a slot start time."""
        hour = start_minutes // 60
        if hour < 12:
            return "Morning"
        if hour < 15:
            return "Midday"
        if hour < 18:
            return "Afternoon"
        if hour < 21:
            return "Evening"
        return "Night"

    def send_plan(self) -> str:
        """Format and return the full schedule as a multi-line string.

        Output sections (in order):
          1. Header — date, scheduled/total counts.
          2. Conflict warnings — printed prominently if detect_conflicts() finds any overlaps.
          3. Critical alert — lists any Priority-1 tasks that could not be scheduled.
          4. Time-window blocks — one block per availability slot, entries sorted by start time,
             with a utilization summary (used/total minutes and percentage) at the end of each block.
          5. Unscheduled tasks — with a suggestion to extend the roomiest slot or re-run after completions.
          6. Pet progress — per-pet done/total task count and completion percentage.
          7. Reasoning log — one bullet per scheduling decision recorded during build_schedule()
             and complete_task().
        """
        width = 52
        total = len(self.scheduled_entries) + len(self.unscheduled_tasks)
        n_scheduled = len(self.scheduled_entries)
        n_unscheduled = len(self.unscheduled_tasks)

        lines = [
            f"PawPal+ Schedule — {self.date}",
            f"{n_scheduled}/{total} tasks scheduled  •  {n_unscheduled} unscheduled",
        ]

        # Conflict detection: warn prominently when overlapping entries exist
        conflicts = self.detect_conflicts()
        if conflicts:
            header = "── [!] SCHEDULE CONFLICTS DETECTED "
            lines.append(f"\n{header.ljust(width, '─')}")
            for c in conflicts:
                lines.append(f"  {c}")

        # Improvement 9: prominent warning if any critical task failed to schedule
        critical_unscheduled = [
            t for t in self.unscheduled_tasks if t.priority == 1]
        if critical_unscheduled:
            header = "── [!] CRITICAL — Unscheduled Priority-1 Tasks "
            lines.append(f"\n{header.ljust(width, '─')}")
            for t in critical_unscheduled:
                lines.append(
                    f"  !! {t.name} ({t.pet_name}) — {t.duration} min NOT SCHEDULED !!")

        # Bucket each ScheduledEntry into its source time window
        slots = self.owner.parse_time_slots()
        raw_slots = self.owner.available_times

        for (start, end), raw in zip(slots, raw_slots):
            label = self._window_label(start)
            header = f"── {label}  {raw} "
            lines.append(f"\n{header.ljust(width, '─')}")

            window_entries = [
                e for e in self.scheduled_entries
                if start <= int(e.scheduled_time[:2]) * 60 + int(e.scheduled_time[3:]) < end
            ]
            window_entries.sort(key=lambda e: e.scheduled_time)

            if window_entries:
                for entry in window_entries:
                    t = entry.task
                    lines.append(
                        f"  {entry.scheduled_time}   "
                        f"{t.name.ljust(16)}"
                        f"{t.pet_name.ljust(12)}"
                        f"{str(t.duration) + ' min':<9}"
                        f"[{t.category}]"
                    )
            else:
                lines.append("  (no tasks scheduled in this window)")

            # Improvement 8: slot utilization report
            used_min = sum(e.task.duration for e in window_entries)
            total_min = end - start
            pct = int(used_min / total_min * 100) if total_min > 0 else 0
            lines.append(f"  Utilization: {used_min}/{total_min} min ({pct}%)")

        # Improvement 4: unscheduled tasks with availability suggestions
        if self.unscheduled_tasks:
            header = "── Could Not Schedule "
            lines.append(f"\n{header.ljust(width, '─')}")

            best_raw, best_free = max(
                self._slot_free_after_build, key=lambda x: x[1]
            ) if self._slot_free_after_build else ("", 0)

            for task in self.unscheduled_tasks:
                lines.append(
                    f"  - {task.name} ({task.pet_name}) — needs {task.duration} min"
                )
                needed = task.duration - best_free
                if needed > 0:
                    lines.append(
                        f"    → Extend your {best_raw} slot by ~{needed} min to fit this task"
                    )
                else:
                    lines.append(
                        f"    → Re-run after marking other tasks complete to free up slot time"
                    )

        # Improvement 10: per-pet completion percentage
        pets_with_tasks = [p for p in self.owner.pets if p.tasks]
        if pets_with_tasks:
            header = "── Pet Progress "
            lines.append(f"\n{header.ljust(width, '─')}")
            for pet in pets_with_tasks:
                done = sum(1 for t in pet.tasks if t.completed)
                total_pet = len(pet.tasks)
                pct = int(done / total_pet * 100)
                lines.append(
                    f"  {pet.name.ljust(12)} {done}/{total_pet} tasks done ({pct}%)"
                )

        if self.reasoning_log:
            header = "── Reasoning "
            lines.append(f"\n{header.ljust(width, '─')}")
            for reason in self.reasoning_log:
                lines.append(f"  • {reason}")

        return "\n".join(lines)
