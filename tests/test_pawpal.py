from pawpal_system import CareTask, Pet
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


def test_mark_complete_changes_status(sample_task):
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_add_task_increases_pet_task_count(sample_pet, sample_task):
    assert len(sample_pet.tasks) == 0
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == 1
