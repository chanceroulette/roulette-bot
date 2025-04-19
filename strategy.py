from collections import Counter
from copy import deepcopy

CHANCE_POOLS = {
    "Rosso": {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "Nero": set(range(0,37)) - {0} - {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
    "Pari": {n for n in range(1,37) if n % 2 == 0},
    "Dispari": {n for n in range(1,37) if n % 2 == 1},
    "Manque": set(range(1,19)),
    "Passe": set(range(19,37)),
}

class StrategyManager:
    def __init__(self, bankroll: int, first15: list[int]):
        self.initial_bankroll = bankroll
        self.current_bankroll = bankroll
        self.first15 = first15.copy()
        self.boxes = {ch: [1] for ch in CHANCE_POOLS}
        self.active = []
        self.total_profit = 0
        self._plays = 0
        self._wins = 0
        self._losses = 0

    def suggested_chances(self) -> list[str]:
        # conta successi nei primi 15
        stats = {ch: 0 for ch in CHANCE_POOLS}
        for n in self.first15:
            for ch, pool in CHANCE_POOLS.items():
                if n in pool:
                    stats[ch] += 1
        # prendi le 3 con meno uscite (più "perdenti")
        sorted_ch = sorted(stats.items(), key=lambda x: x[1])
        self.active = [ch for ch, _ in sorted_ch[:3]]
        return self.active

    def play(self, number: int) -> tuple[int, dict]:
        bets = {}
        outcomes = {}
        profit = 0

        for ch in self.active:
            pool = CHANCE_POOLS[ch]
            box = self.boxes[ch]
            # puntata = somma prima + ultima casella
            bet = box[0] + (box[-1] if len(box) > 1 else 0)
            win = number in pool
            res = bet if win else -bet
            outcomes[ch] = (bet, res)
            profit += res
            self.total_profit += res

            # aggiorna box
            if win:
                self._wins += 1
                if len(box) > 1:
                    new_box = box[1:-1]
                    self.boxes[ch] = new_box if new_box else [1]
                else:
                    self.boxes[ch] = [1]
            else:
                self._losses += 1
                box.append(bet)
                self.boxes[ch] = box

        self._plays += 1
        self.current_bankroll += profit
        return profit, outcomes

    def total_plays(self) -> int:
        return self._plays

    def wins_losses(self) -> tuple[int,int]:
        return self._wins, self._losses