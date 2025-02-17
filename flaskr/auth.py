from functools import wraps

from flask import request, make_response, jsonify


def authenticate():
    response = make_response(jsonify({"message": "Authentication required"}), 401)
    response.headers["WWW-Authenticate"] = 'Basic realm="Login Required"'
    return response


def authenticate_user(username, password):
    if username == "admin" and password == "admin":
        return True
    return False


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        if not auth or not authenticate_user(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated
