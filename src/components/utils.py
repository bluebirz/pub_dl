import uuid
from datetime import datetime


def gen_id(prefix: str = None) -> str:
    if prefix:
        return f"{prefix}-{str(uuid.uuid4()).split('-')[-1]}"
    else:
        return f"{str(uuid.uuid4()).split('-')[-1]}"


def get_current_time_str(format: str = "%F") -> str:
    """return string of datetime

    Args:
        format: `%F` for 'YYYY-mm-DD'
            or `%F_%X` for 'YYYY-mm-DD_HH:MM:SS'

    Returns:
        string of datetime
    """
    return datetime.now().strftime(format)
