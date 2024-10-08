import random


def get_random_time_in_timeframe(from_hour: int, to_hour: int) -> str:
    if from_hour == to_hour:
        raise ("Invalid timeframe. Must be at least 1 hour long.")
    total_minutes_in_timeframe = (to_hour - from_hour) * 60
    rand_num_minutes = random.randint(0, total_minutes_in_timeframe)
    hour_offset, minute_offset = divmod(rand_num_minutes, 60)

    generated_hour = from_hour + hour_offset

    if generated_hour < 10:
        generated_hour_str = f"0{generated_hour}"
    else:
        generated_hour_str = str(generated_hour)

    if minute_offset < 10:
        minute_offset_str = f"0{minute_offset}"
    else:
        minute_offset_str = str(minute_offset)

    return f"{generated_hour_str}:{minute_offset_str}"
