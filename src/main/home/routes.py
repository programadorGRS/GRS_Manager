from flask import render_template
from flask_login import login_required

from src import app


@app.route('/home')
@login_required
def home():
    power_bi_url = app.config.get("HOME_DASHBOARD_URL")
    return render_template('home.html', title='GRS+Connect', power_bi_url=power_bi_url)
