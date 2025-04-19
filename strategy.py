from collections import defaultdict, deque

class StrategyManager:
    def __init__(self):
        self.initial   = defaultdict(list)
        self.session   = {}
        self.history   = defaultdict(list)
        self.boxes     = defaultdict(lambda: {
            "rosso": deque([1]), "nero": deque([1]),
            "pari": deque([1]), "dispari": deque([1]),
            "manque": deque([1]), "passe": deque([1]),
        })
        self.balance      = defaultdict(int)
        self.play_count   = defaultdict(int)

    def reset_session(self, uid):
        self.initial[uid].clear()
        self.history[uid].clear()
        for k in self.boxes[uid]:
            self.boxes[uid][k] = deque([1])
        self.balance[uid]    = 0
        self.play_count[uid] = 0
        self.session[uid]    = False

    def add_initial_number(self, uid, n):
        self.initial[uid].append(n)
        return len(self.initial[uid])

    def has_initial(self, uid):
        return len(self.initial[uid]) >= 15

    def analyze_initial(self, uid):
        counts = {c:0 for c in self.boxes[uid]}
        for n in self.initial[uid]:
            if n==0: continue
            counts["rosso" if n%2==1 else "nero"] += 1
            counts["pari"  if n%2==0 else "dispari"] += 1
            counts["manque" if 1<=n<=18 else "passe"] += 1
        return sorted(counts, key=lambda c: counts[c])[:3]

    def start_session(self, uid):
        self.session[uid] = True

    def in_session(self, uid):
        return self.session.get(uid, False)

    def process_number(self, uid, n):
        lines = [f"NUMERO USCITO: {n}"]
        self.play_count[uid] += 1
        for chance, box in self.boxes[uid].items():
            win = (
                (chance=="rosso"   and n%2==1) or
                (chance=="nero"    and n%2==0 and n!=0) or
                (chance=="pari"    and n%2==0 and n!=0) or
                (chance=="dispari" and n%2==1) or
                (chance=="manque"  and 1<=n<=18) or
                (chance=="passe"   and 19<=n<=36)
            )
            stake = box[0] + box[-1] if len(box)>1 else box[0]
            if win:
                self.balance[uid] += stake
                if len(box)>1:
                    box.popleft(); box.pop()
                result = f"+{stake}"
            else:
                self.balance[uid] -= stake
                box.append(stake)
                result = f"-{stake}"
            lines.append(f"{chance.capitalize()}: puntate {stake} → esito: {result}")
        lines.append(f"Saldo totale: {self.balance[uid]} fiche")
        self.history[uid].append(n)
        return "\n".join(lines)

    def build_session_report(self, uid):
        return (
            f"REPORT SESSIONE\n"
            f"Giocate totali: {self.play_count[uid]}\n"
            f"Saldo: {self.balance[uid]}\n"
            f"Numeri usciti: {', '.join(map(str,self.history[uid]))}"
        )

    def undo_last(self, uid):
        if not self.history[uid]:
            return "Niente da annullare."
        last = self.history[uid].pop()
        nums = self.history[uid][:]
        self.reset_session(uid)
        for n in self.initial[uid]:
            pass
        for x in nums:
            self.process_number(uid, x)
        return f"Ultima estrazione ({last}) annullata."
