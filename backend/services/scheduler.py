import random

def today_send_plan(daily_target: int) -> list[int]:
    """
    Return minutes-from-midnight slots between 09:00–17:00.
    """
    start, end = 9*60, 17*60
    target = max(1, daily_target)
    k = min(target, max(1, end - start))
    return sorted(random.sample(range(start, end), k=k))
