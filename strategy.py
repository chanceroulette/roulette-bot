from collections import defaultdict

def inizializza_box():
    return [1, 1, 1, 1]

class StrategiaRoulette:
    def __init__(self):
        self.chances_attive = []  # es. ["Rosso", "Pari", "Passe"]
        self.box = defaultdict(inizializza_box)
        self.vinte = 0
        self.perse = 0
        self.saldo = 0

    def attiva_chances(self, lista_chances):
        self.chances_attive = lista_chances
        for chance in lista_chances:
            if chance not in self.box or not self.box[chance]:
                self.box[chance] = inizializza_box()

    def calcola_puntate(self):
        puntate = {}
        for chance in self.chances_attive:
            box = self.box[chance]
            if len(box) == 1:
                puntate[chance] = box[0]
            else:
                puntate[chance] = box[0] + box[-1]
        return puntate

    def aggiorna_esito(self, numero_uscito):
        risultati = {}
        for chance in self.chances_attive:
            fiche_giocate = self.calcola_puntate()[chance]
            vincente = self.numero_in_chance(numero_uscito, chance)

            if vincente:
                # vinco, tolgo prima e ultima
                if len(self.box[chance]) > 1:
                    self.box[chance] = self.box[chance][1:-1]
                else:
                    self.box[chance] = []
                self.vinte += fiche_giocate
                self.saldo += fiche_giocate
                risultati[chance] = f"+{fiche_giocate}"
            else:
                # perdo, aggiungo in fondo
                self.box[chance].append(fiche_giocate)
                self.perse += fiche_giocate
                self.saldo -= fiche_giocate
                risultati[chance] = f"-{fiche_giocate}"

            # se box si svuota, lo ricreo
            if not self.box[chance]:
                self.box[chance] = inizializza_box()

        return risultati

    def numero_in_chance(self, numero, chance):
        mapping = {
            'Rosso': [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
            'Nero': [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35],
            'Pari': [x for x in range(1, 37) if x % 2 == 0],
            'Dispari': [x for x in range(1, 37) if x % 2 != 0],
            'Manque': list(range(1, 19)),
            'Passe': list(range(19, 37))
        }
        return numero in mapping.get(chance, [])