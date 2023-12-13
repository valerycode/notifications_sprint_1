from datetime import datetime


def get_ttl_from_datetime(dt: datetime) -> int:
    """Возвращает разницу между переданной меткой и текущим временем"""
    return int(dt.timestamp() - datetime.utcnow().timestamp())
