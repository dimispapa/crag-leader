"""
Scheduled task for weekly data updates
"""
import asyncio
from worker import worker_process


def scheduled_update():
    """Run the scheduled update task"""
    asyncio.run(worker_process())


if __name__ == "__main__":
    scheduled_update()
