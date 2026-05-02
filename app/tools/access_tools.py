def check_user_access(user_id, app):
    return {"has_access": False}

def check_account_locked(user_id):
    return {"locked": False}

def check_account_exists(user_id):
    return {"exists": True}

def grant_access(user_id, app):
    return {"status": "granted"}