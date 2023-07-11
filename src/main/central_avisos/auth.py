from functools import wraps

import jwt
from flask import abort, current_app, request


def validate_token(token: str):
    try:
        data = jwt.decode(jwt=token, key=current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return data
    except jwt.InvalidTokenError:  # base exception for decode errors
        return None


def filter_token_required(func):
    '''Validates the token and passes its data to the route'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.args.get(key="token", type=str)

        if not token:
            return abort(404)

        token_data = validate_token(token=token)

        if not token_data:
            return abort(404)

        return func(token, token_data, *args, **kwargs)

    return wrapper
