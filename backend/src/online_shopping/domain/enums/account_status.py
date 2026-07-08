from enum import Enum


class AccountStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    BANNED = "banned"
    COMPROMISED = "compromised"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"

    Active = ACTIVE
    Blocked = BLOCKED
    Banned = BANNED
    Compromised = COMPROMISED
    Archived = ARCHIVED
    Unknown = UNKNOWN
