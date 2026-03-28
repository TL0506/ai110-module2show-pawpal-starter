import pytest
from pawpal_system import Pet, Task, TaskType, Frequency


# ------------------------------------------------------------------
# Shared fixtures — reusable test objects
# ------------------------------------------------------------------

@pytest.fixture
def sample_task():
    """A basic walking task, starts incomplete."""
    return Task(
        task_type=TaskType.WALKING,
        description="Morning walk",
        duration_minutes=30,
        priority="medium",
        frequency=Frequency.DAILY,
    )


@pytest.fixture
def sample_pet():
    """A dog with no tasks yet."""
    return Pet(name="Buddy", breed="Golden Retriever", type="dog", priority=1)


# ------------------------------------------------------------------
# Test 1 — Task Completion
# ------------------------------------------------------------------

def test_task_completion_changes_status(sample_task):
    """Calling complete() should flip is_completed from False to True."""
    assert sample_task.is_completed is False   # starts incomplete
    sample_task.complete()
    assert sample_task.is_completed is True    # now marked done


# ------------------------------------------------------------------
# Test 2 — Task Addition
# ------------------------------------------------------------------

def test_adding_task_increases_pet_task_count(sample_pet, sample_task):
    """Adding a task to a Pet should increase its task list by exactly one."""
    before = len(sample_pet.get_tasks())
    sample_pet.add_task(sample_task)
    after = len(sample_pet.get_tasks())
    assert after == before + 1
