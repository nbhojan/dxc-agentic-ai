import re


_WORD_RE = re.compile(r"\b\w+\b")
_PRIORITY_LEVELS = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
_LEVEL_PRIORITIES = {value: key for key, value in _PRIORITY_LEVELS.items()}
_SLA_HOURS = {"P1": 2, "P2": 8, "P3": 24, "P4": 72}


def _words(text):
    return {match.group(0).lower() for match in _WORD_RE.finditer(text)}


def _has_any(words, candidates):
    return any(candidate in words for candidate in candidates)


def triage(ticket: dict) -> dict:
    title = ticket.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required")

    description = ticket.get("description")
    if description is None:
        description = ""
    if not isinstance(description, str):
        description = str(description)

    affected_users = ticket.get("affected_users", 1)
    if not isinstance(affected_users, int) or affected_users < 1:
        raise ValueError("affected_users must be a positive integer")

    customer_tier = ticket.get("customer_tier", "standard")
    if customer_tier not in {"standard", "vip"}:
        raise ValueError("customer_tier must be standard or vip")

    text = f"{title} {description}".lower()
    words = _words(text)

    if affected_users >= 50 or _has_any(words, {"outage", "down"}) or "outage" in text or "down" in text:
        priority = "P1"
    elif affected_users >= 10 or _has_any(words, {"urgent", "blocked"}) or "urgent" in text or "blocked" in text:
        priority = "P2"
    elif affected_users >= 2:
        priority = "P3"
    else:
        priority = "P4"

    if customer_tier == "vip":
        priority = _LEVEL_PRIORITIES[max(1, _PRIORITY_LEVELS[priority] - 1)]

    if _has_any(words, {"phishing", "breach", "malware"}):
        queue = "Security"
    elif _has_any(words, {"vpn", "wifi", "network"}):
        queue = "Network"
    elif _has_any(words, {"password", "login", "locked"}):
        queue = "Access"
    elif _has_any(words, {"laptop", "keyboard", "screen"}):
        queue = "Hardware"
    else:
        queue = "General"

    return {"priority": priority, "queue": queue, "sla_hours": _SLA_HOURS[priority]}
