def build_session_report(session_data):
    report = "Numeri usciti:\n"
    numeri = session_data.get("numeri", [])
    if not numeri:
        report += "Nessun numero inserito."
        return report

    report += ", ".join(str(n) for n in numeri)

    saldo = session_data.get("saldo", 0)
    report += f"\n\nSaldo totale: {saldo} fiche"

    return report


def suggerisci_chances(numeri):
    if len(numeri) < 15:
        return []

    stats = {
        "rosso": 0,
        "nero": 0,
        "pari": 0,
        "dispari": 0,
        "manque": 0,  # 1–18
        "passe": 0,   # 19–36
    }

    rosso = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    nero = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

    for n in numeri[-15:]:
        if n in rosso:
            stats["rosso"] += 1
        if n in nero:
            stats["nero"] += 1
        if n % 2 == 0:
            stats["pari"] += 1
        else:
            stats["dispari"] += 1
        if 1 <= n <= 18:
            stats["manque"] += 1
        elif 19 <= n <= 36:
            stats["passe"] += 1

    max_val = max(stats.values())
    chances = [k for k, v in stats.items() if v == max_val]

    return chances


def calcola_esito(numero, chances_attive, box):
    esiti = {}
    fiches_totali = 0
    fiches_vinte = 0

    rosso = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    nero = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

    for chance in chances_attive:
        box_chance = box.get(chance, [1, 1, 1, 1])
        if len(box_chance) < 2:
            puntata = 1
        else:
            puntata = box_chance[0] + box_chance[-1]

        fiches_totali += puntata
        vinta = False

        if chance == "rosso" and numero in rosso:
            vinta = True
        elif chance == "nero" and numero in nero:
            vinta = True
        elif chance == "pari" and numero % 2 == 0:
            vinta = True
        elif chance == "dispari" and numero % 2 == 1:
            vinta = True
        elif chance == "manque" and 1 <= numero <= 18:
            vinta = True
        elif chance == "passe" and 19 <= numero <= 36:
            vinta = True

        if vinta:
            esiti[chance] = f"+{puntata}"
            fiches_vinte += puntata
            if len(box_chance) > 2:
                box_chance = box_chance[1:-1]
            else:
                box_chance = [1, 1, 1, 1]
        else:
            esiti[chance] = f"-{puntata}"
            box_chance.append(puntata)

        box[chance] = box_chance

    saldo = fiches_vinte - fiches_totali
    return esiti, saldo, box