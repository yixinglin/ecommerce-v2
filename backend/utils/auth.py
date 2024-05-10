import base64


def basic_auth(username, password):
    auth = f"{username}:{password}"
    auth = base64.b64encode(auth.encode()).decode()
    return f"Basic {auth}"

