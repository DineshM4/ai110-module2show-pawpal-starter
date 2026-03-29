from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class CareTask:
    name: str
    category: str  # e.g. "Grooming", "Feeding", "Medical"
    duration: int  # in minutes
    priority: int  # 1 = Critical, 2 = Important, 3 = Optional
    # set when task is added to a Pet; preserves identity after gather_all_tasks
    pet_name: str = ""
    completed: bool = False

    def update_priority(self, priority: int) -> None:
        """Set the task's priority level (1=Critical, 2=Important, 3=Optional)."""
        self.priority = priority

    def update_duration(self, duration: int) -> None:
        """Update the estimated duration of the task in minutes."""
        self.duration = duration

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True


@dataclass
class ScheduledEntry:
    """Wraps a CareTask with a concrete time slot so the schedule records *when* each task runs."""
    task: CareTask
    scheduled_time: str  # e.g. "08:00"


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
        self.name = name
        # e.g. ["08:00-09:00", "17:00-18:00"]
        self.available_times = available_times
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's roster."""
        self.pets.append(pet)

    def update_availability(self, times: List[str]) -> None:
        """Replace the owner's available time slots with a new list of 'HH:MM-HH:MM' strings."""
        self.available_times = times

    def parse_time_slots(self) -> List[Tuple[int, int]]:
        """Parse each 'HH:MM-HH:MM' availability string into a (start_minutes, end_minutes) tuple."""
        slots = []
        for slot in self.available_times:
            start_str, end_str = slot.split("-")
            sh, sm = map(int, start_str.split(":"))
            eh, em = map(int, end_str.split(":"))
            slots.append((sh * 60 + sm, eh * 60 + em))
        return slots


class Scheduler:
    def __init__(self, owner: Owner, date: str):
        self.owner = owner
        self.date = date
        self.all_tasks: List[CareTask] = []
        # replaces scheduled_tasks; carries time info
        self.scheduled_entries: List[ScheduledEntry] = []
        self.unscheduled_tasks: List[CareTask] = []
        self.reasoning_log: List[str] = []

    def gather_all_tasks(self) -> None:
        """Rebuild all_tasks by collecting every CareTask across all of the owner's pets."""
        self.all_tasks = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                # keep pet_name in sync even if task was created before being added
                task.pet_name = pet.name
                self.all_tasks.append(task)

    def build_schedule(self) -> None:
        """Sort all tasks by priority then duration, fit them into the owner's time slots, and log reasoning."""
        self.scheduled_entries = []
        self.unscheduled_tasks = []
        self.reasoning_log = []

        self.gather_all_tasks()

        # Sort by priority (1=Critical first), then by duration ascending to fit more tasks per slot
        sorted_tasks = sorted(
            self.all_tasks, key=lambda t: (t.priority, t.duration))

        # Convert time slot strings to (cursor_minutes, end_minutes) pairs
        slot_cursors: List[List[int]] = [
            [start, end] for start, end in self.owner.parse_time_slots()
        ]

        for task in sorted_tasks:
            scheduled = False
            for slot in slot_cursors:
                cursor, end = slot
                if end - cursor >= task.duration:
                    scheduled_time = f"{cursor // 60:02d}:{cursor % 60:02d}"
                    self.scheduled_entries.append(ScheduledEntry(
                        task=task, scheduled_time=scheduled_time))
                    # advance cursor within this slot
                    slot[0] = cursor + task.duration
                    self.reasoning_log.append(
                        f"Scheduled '{task.name}' ({task.pet_name}) at {scheduled_time} "
                        f"[priority {task.priority}, {task.duration} min]"
                    )
                    scheduled = True
                    break

            if not scheduled:
                self.unscheduled_tasks.append(task)
                self.reasoning_log.append(
                    f"Could not schedule '{task.name}' ({task.pet_name}) "
                    f"[priority {task.priority}, {task.duration} min] — no available slot fits"
                )

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
        """Format and return the full schedule — grouped by time window — including unscheduled tasks and reasoning log."""
        width = 52
        total = len(self.scheduled_entries) + len(self.unscheduled_tasks)
        n_scheduled = len(self.scheduled_entries)
        n_unscheduled = len(self.unscheduled_tasks)

        lines = [
            f"PawPal+ Schedule — {self.date}",
            f"{n_scheduled}/{total} tasks scheduled  •  {n_unscheduled} unscheduled",
        ]

        # Bucket each ScheduledEntry into its source time window
        slots = self.owner.parse_time_slots()
        raw_slots = self.owner.available_times  # original "HH:MM-HH:MM" strings

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

        if self.unscheduled_tasks:
            header = "── Could Not Schedule "
            lines.append(f"\n{header.ljust(width, '─')}")
            for task in self.unscheduled_tasks:
                lines.append(
                    f"  - {task.name} ({task.pet_name}) — needs {task.duration} min")

        if self.reasoning_log:
            header = "── Reasoning "
            lines.append(f"\n{header.ljust(width, '─')}")
            for reason in self.reasoning_log:
                lines.append(f"  • {reason}")

        return "\n".join(lines)
