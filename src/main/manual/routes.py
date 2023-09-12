from flask import Blueprint, render_template
from flask_login import login_required

manual_bp = Blueprint(
    name="manual",
    import_name=__name__,
    url_prefix="/manual",
    template_folder="templates",
)


@manual_bp.route("/")
@login_required
def manual():
    return render_template("manual/manual.html")
