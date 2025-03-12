"""
Scheduled task for weekly data updates
"""
from worker import worker_task


def scheduled_update():
    """Run the scheduled update task"""
    worker_task()


if __name__ == "__main__":
    scheduled_update()
