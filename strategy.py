# strategy.py

RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = set(range(1,37)) - RED
EVEN  = {n for n in range(1,37) if n % 2 == 0}
ODD   = set(range(1,37)) - EVEN
MANQUE = set(range(1,19))
PASSE  = set(range(19,37))

ALL_CHANCES = {
    "rosso": RED,
    "nero": BLACK,
    "pari": EVEN,
    "dispari": ODD,
    "manque": MANQUE,
    "passe": PASSE,
}

def suggerisci_chances(numeri15):
    """
    Analizza i primi 15 numeri e restituisce le chances con più successi.
    """
    consigliate = []
    for nome, insieme in ALL_CHANCES.items():
        successi = sum(1 for n in numeri15 if n in insieme)
        insuccessi = len(numeri15) - successi
        if successi >= insuccessi:
            consigliate.append(nome)
    return consigliate

def build_session_report(data):
    """
    Crea un report della sessione corrente.
    """
    righe = [
        "▶️ REPORT SESSIONE ◀️",
        f"Totale giocate: {data['games']}",
        f"Vittorie: {data['wins']} | Sconfitte: {data['losses']}",
        f"Saldo totale: {data['saldo']} fiche",
        f"Chances attive: {', '.join(data['chances_attive'])}",
        "Box attuali per ciascuna chance:"
    ]
    for chance, box in data["box"].items():
        righe.append(f"  - {chance.capitalize()}: {box}")
    return "\n".join(righe)

def calcola_esito(numero, data):
    """
    Calcola l’esito del numero uscito, aggiorna i box e il saldo.
    """
    saldo_giro = 0
    risultati = [f"NUMERO USCITO: {numero}"]
    for chance in data["chances_attive"]:
        insieme = ALL_CHANCES[chance]
        box = data["box"].get(chance, [1, 1, 1, 1])

        stake = box[0] + box[-1] if len(box) > 1 else box[0]
        vinta = numero in insieme

        if vinta:
            box = box[1:-1] if len(box) > 2 else [1, 1, 1, 1]
            data["wins"] += 1
            risultato = f"+{stake}"
            saldo_giro += stake
        else:
            box.append(stake)
            data["losses"] += 1
            risultato = f"-{stake}"
            saldo_giro -= stake

        data["box"][chance] = box
        risultati.append(f"{chance.capitalize()}: puntate {stake} fiche → esito: {risultato}")

    data["saldo"] += saldo_giro
    risultati.append(f"\nSaldo attuale: {data['saldo']} fiche")
    return "\n".join(risultati)