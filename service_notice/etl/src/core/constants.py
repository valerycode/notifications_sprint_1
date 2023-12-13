from enum import Enum

QUEUE_NOTICE = "notice"


class Mark(Enum):
    REJECTED_USER = 0
    REJECTED_NODATA = 1
    QUEUED = 2
    SENT = 3


class Transport(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBSOCKET = "websocket"
    PUSH = "push"
