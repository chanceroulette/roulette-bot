from collections import defaultdict, deque

CHANCES = {
    "rosso": [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
    "nero": [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
    "pari": [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36],
    "dispari": [1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35],
    "manque": list(range(1, 19)),
    "passe": list(range(19, 37))
}

class StrategyManager:
    def __init__(self):
        self.box = defaultdict(list)  # uno per ogni chance attiva
        self.storico = []
        self.primi_15 = []
        self.saldo = 0

    def reset(self):
        self.box = defaultdict(list)
        self.storico = []
        self.primi_15 = []
        self.saldo = 0

    def annulla_ultimo(self):
        if self.storico:
            self.storico.pop()
        for chance in self.box:
            if self.box[chance]:
                self.box[chance].pop()

    def genera_report(self, numero, chances_attive):
        report = []
        self.storico.append(numero)
        totale = 0

        for chance in chances_attive:
            vincente = numero in CHANCES[chance]
            box = self.box[chance]

            # se il box è vuoto, ricrealo da 1 a 4
            if not box:
                box.extend([1, 2, 3, 4])

            puntata = box[0] + box[-1] if len(box) > 1 else box[0]
            if vincente:
                guadagno = puntata
                report.append(f"{chance.capitalize()}: puntate {puntata} fiche → esito: +{guadagno}")
                box = box[1:-1]  # rimuove prima e ultima
            else:
                perdita = puntata
                report.append(f"{chance.capitalize()}: puntate {puntata} fiche → esito: -{perdita}")
                box.append(puntata)

            self.box[chance] = box
            totale += guadagno if vincente else -perdita

        self.saldo += totale
        report.append(f"\nSaldo totale: {self.saldo} fiche")
        return "\n".join(report)

def get_chances_from_numbers(numeri):
    conteggi = defaultdict(int)
    for numero in numeri:
        for chance, lista in CHANCES.items():
            if numero in lista:
                conteggi[chance] += 1
    # ritorna le 3 chances più frequenti
    scelte = sorted(conteggi.items(), key=lambda x: x[1], reverse=True)[:3]
    return [c[0] for c in scelte]

def should_suggest_change(storico, chances_attive):
    if len(storico) < 20:
        return None

    ultimi_15 = storico[-15:]
    nuove = get_chances_from_numbers(ultimi_15)

    suggerimenti = []
    for chance in nuove:
        if chance not in chances_attive:
            suggerimenti.append(f"Aggiungi {chance}")
    for chance in chances_attive:
        if chance not in nuove:
            suggerimenti.append(f"Valuta di rimuovere {chance}")

    if suggerimenti:
        return ", ".join(suggerimenti)
    return None