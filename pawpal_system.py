from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class CareTask:
    name: str
    category: str  # e.g. "Grooming", "Feeding", "Medical"
    duration: int  # in minutes
    priority: int  # 1 = Critical, 2 = Important, 3 = Optional

    def update_priority(self, priority: int) -> None:
        pass

    def update_duration(self, duration: int) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        pass

    def remove_task(self, task: CareTask) -> None:
        pass


class Owner:
    def __init__(self, name: str, available_times: List[str], preferences: Dict):
        self.name = name
        self.available_times = available_times  # e.g. ["08:00-09:00", "17:00-18:00"]
        self.preferences = preferences
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def update_availability(self, times: List[str]) -> None:
        pass


class Scheduler:
    def __init__(self, owner: Owner, date: str):
        self.owner = owner
        self.date = date
        self.all_tasks: List[CareTask] = []
        self.scheduled_tasks: List[CareTask] = []
        self.unscheduled_tasks: List[CareTask] = []
        self.reasoning_log: List[str] = []

    def gather_all_tasks(self) -> None:
        pass

    def build_schedule(self) -> None:
        pass

    def send_plan(self) -> None:
        pass
