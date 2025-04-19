class StrategyManager:
    def __init__(self, first15: list[int]):
        self.first15 = first15.copy()
        self.boxes = { 
            "Rosso": [1,1,1,1],
            "Nero": [1,1,1,1],
            "Pari": [1,1,1,1],
            "Dispari":[1,1,1,1],
            "Passe":[1,1,1,1],
            "Manque":[1,1,1,1],
        }
        self._plays = 0
        self._wins = 0
        self._losses = 0

    def suggested_chances(self) -> list[str]:
        """Conta successi in first15 e restituisce le top3."""
        stats = {}
        for chance, pool in self.boxes.items():
            stats[chance] = sum(1 for n in self.first15 if self._in_pool(n, chance))
        # prendi le 3 con più successi
        return sorted(stats, key=lambda c: stats[c], reverse=True)[:3]

    def play(self, number: int) -> tuple[int, dict]:
        """Applica un giro di puntate solo su chances consigliate."""
        total = 0
        details = {}
        for chance in self.suggested_chances():
            box = self.boxes[chance]
            bet = box[0] + box[-1] if len(box)>1 else box[0]
            win = self._in_pool(number, chance)
            res = bet if win else -bet
            total += res
            details[chance] = (bet, res)
            if win:
                self._wins += 1
                # rimuovi estremo
                if len(box)>2:
                    box.pop(0); box.pop(-1)
                else:
                    box[:] = [1,1,1,1]
            else:
                self._losses += 1
                box.append(bet)
            self.boxes[chance] = box
        self._plays += 1
        return total, details

    def total_plays(self) -> int:
        return self._plays

    def wins_losses(self) -> tuple[int,int]:
        return self._wins, self._losses

    @staticmethod
    def _in_pool(n: int, chance: str) -> bool:
        pools = {
            "Rosso": {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
            "Nero": set(range(1,37)) - {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36},
            "Pari": {n for n in range(1,37) if n%2==0},
            "Dispari": {n for n in range(1,37) if n%2==1},
            "Manque": set(range(1,19)),
            "Passe": set(range(19,37)),
        }
        return n in pools[chance]