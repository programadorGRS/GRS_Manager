from flask import render_template
from flask_login import login_required

from src import app


@app.route('/manual')
@login_required
def manual():
    return render_template('manual.html', title='GRS+Connect')
