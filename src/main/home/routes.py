from flask import Blueprint, render_template
from flask_login import login_required

from src import app

home_bp = Blueprint(
    name="home",
    import_name=__name__,
    url_prefix="/home",
    template_folder="templates",
)


@home_bp.route("/")
@login_required
def home():
    power_bi_url = app.config.get("HOME_DASHBOARD_URL")
    return render_template("home/home.html", power_bi_url=power_bi_url)
