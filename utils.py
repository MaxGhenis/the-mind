import random


def generate_fun_name():
    adjectives = [
        "Clever",
        "Witty",
        "Brainy",
        "Quirky",
        "Zany",
        "Sassy",
        "Nerdy",
        "Goofy",
        "Peppy",
        "Spunky",
    ]
    nouns = [
        "Bot",
        "AI",
        "Thinker",
        "Whiz",
        "Genius",
        "Mind",
        "Brain",
        "Sage",
        "Guru",
        "Maven",
    ]
    return f"{random.choice(adjectives)} {random.choice(nouns)}"
