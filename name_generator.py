import random


def generate_unique_fun_names(num_players):
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

    if num_players > min(len(adjectives), len(nouns)):
        raise ValueError(
            "Not enough unique combinations for the requested number of players"
        )

    used_adjectives = set()
    used_nouns = set()
    names = []

    for _ in range(num_players):
        while True:
            adj = random.choice(adjectives)
            noun = random.choice(nouns)
            if adj not in used_adjectives and noun not in used_nouns:
                used_adjectives.add(adj)
                used_nouns.add(noun)
                names.append(f"{adj} {noun}")
                break

    return names


# Usage example:
# player_names = generate_unique_fun_names(5)
# for name in player_names:
#     print(name)
