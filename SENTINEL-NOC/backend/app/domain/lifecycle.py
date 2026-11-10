from enum import StrEnum


class Severity(StrEnum):
    OK = "OK"
    WARN = "WARN"
    CRIT = "CRIT"
    UNKNOWN = "UNKNOWN"
    RECOVERY = "RECOVERY"


class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


TRANSITIONS = {
    "OPEN": {"ACKNOWLEDGED", "INVESTIGATING", "RESOLVED"},
    "ACKNOWLEDGED": {"INVESTIGATING", "RESOLVED"},
    "INVESTIGATING": {"RESOLVED"},
    "RESOLVED": {"OPEN", "CLOSED"},
    "CLOSED": set(),
}
ACTIVE = {"OPEN", "ACKNOWLEDGED", "INVESTIGATING"}
HEALTHY = {"OK", "RECOVERY"}


def transition_allowed(current: str, target: str) -> bool:
    return target in TRANSITIONS[current]


def count_transitions(states: list[str]) -> int:
    normalized = ["OK" if state in HEALTHY else state for state in states]
    return sum(a != b for a, b in zip(normalized, normalized[1:], strict=False))
