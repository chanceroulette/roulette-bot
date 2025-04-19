user_data = {}
user_ids = set()

def init_user(user_id):
    user_ids.add(user_id)
    user_data[user_id] = {
        "boxes": {},
        "history": [],
        "active_chances": [],
        "suggested_chances": [],
        "turns": 0,
        "fiches_won": 0,
        "fiches_lost": 0,
        "input_sequence": [],
        "is_ready": False,
        "pending_selection": False
    }
