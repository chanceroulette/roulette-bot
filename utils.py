CHANCES = {
    "Rosso": {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36},
    "Nero": {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35},
    "Pari": {n for n in range(1, 37) if n % 2 == 0},
    "Dispari": {n for n in range(1, 37) if n % 2 != 0},
    "Manque": set(range(1, 19)),
    "Passe": set(range(19, 37)),
}

CHANCE_ORDER = ["Manque", "Pari", "Rosso", "Nero", "Dispari", "Passe"]

def suggest_chances(numbers):
    count = {chance: 0 for chance in CHANCE_ORDER}
    for n in numbers:
        for chance, values in CHANCES.items():
            if n in values:
                count[chance] += 1
    sorted_by_least = sorted(count.items(), key=lambda x: x[1])
    selected = [c[0] for c in sorted_by_least[:6]]
    ordered_selection = [ch for ch in CHANCE_ORDER if ch in selected]
    return ordered_selection[:max(2, len(ordered_selection))]

def get_win(chance, number):
    return number in CHANCES[chance]

def format_box(box):
    return " | ".join(str(int(x)) for x in box)

def init_box():
    return [1, 1, 1, 1]
