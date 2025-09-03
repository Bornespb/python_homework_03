import random


def get_score(
    store: dict | None,
    phone: str | None,
    email: str | None,
    birthday: str | None,
    gender: int | None,
    first_name: str | None,
    last_name: str | None,
) -> float:
    score = 0.0
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    return score


def get_interests(store: dict | None, cid: int) -> list[str]:
    interests = [
        "cars",
        "pets",
        "travel",
        "hi-tech",
        "sport",
        "music",
        "books",
        "tv",
        "cinema",
        "geek",
        "otus",
    ]
    return random.sample(interests, 2)
