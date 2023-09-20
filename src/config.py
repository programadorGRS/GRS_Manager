import json
from typing import Literal

from flask import Flask


def set_app_config(app: Flask, conf: Literal["prod", "dev"]):
    """Changes app config between dev/prod"""
    match conf:
        case "prod":
            # using mysql
            app.config.from_file("../configs/prod.json", load=json.load)
        case "dev":
            # using sqlite
            app.config.from_file("../configs/dev.json", load=json.load)
    return None
