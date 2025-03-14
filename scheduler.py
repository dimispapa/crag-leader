"""
Scheduled task for weekly data updates
"""
from worker import main


def scheduled_update():
    """Run the scheduled update task"""
    main()


if __name__ == "__main__":
    scheduled_update()
