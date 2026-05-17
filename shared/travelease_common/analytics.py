from __future__ import annotations

POSITIVE_WORDS = {
    "great",
    "amazing",
    "excellent",
    "clean",
    "friendly",
    "быстро",
    "классно",
    "чисто",
    "удобно",
    "отлично",
}
NEGATIVE_WORDS = {
    "bad",
    "slow",
    "dirty",
    "noisy",
    "repetitive",
    "грязно",
    "шумно",
    "медленно",
    "плохо",
}


def conversion_rate(search_count: int, booking_count: int) -> float:
    if search_count <= 0:
        return 0.0
    return round((booking_count / search_count) * 100, 2)


def sentiment_score(text: str) -> float:
    words = text.lower().replace(".", " ").replace(",", " ").split()
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    raw = pos - neg
    return round(raw / max(len(words), 1), 3)


def sentiment_label(score: float) -> str:
    if score > 0.03:
        return "positive"
    if score < -0.03:
        return "negative"
    return "neutral"
