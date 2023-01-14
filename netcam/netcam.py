# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

from flask import Flask
from flask import render_template
from flask import url_for

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    return render_template(
        template_name_or_list='home.html',
        navigation={
            "icon": "hamburger",
            "url": url_for("menu_main", _external=True) }
    )

@app.route("/menu/main")
def menu_main():
    return render_template(
        template_name_or_list='menu.main.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )

@app.route("/tiles")
def tiles():
    return render_template(
        template_name_or_list='tiles.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )

@app.route("/menu/clips")
def menu_clips():
    return render_template(
        template_name_or_list='menu.clips.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )

@app.route("/clips/<period>")
def clips(period):
    return render_template(
        template_name_or_list='clips.html',
        period=period,
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )

@app.route("/clip/<clipdate>/<cliptime>")
def clip(clipdate, cliptime):
    """
        render the videoclip defined by clipdate and cliptime
    :param clipdate: string, format: yyyy-mm-dd
    :param cliptime: string, format: hh:mm:ss.mmm
    :return: template rendered with information
    """
    return render_template(
        template_name_or_list='clip.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )

@app.route("/states")
def states():
    return render_template(
        template_name_or_list='states.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )

@app.route("/logs")
def logs():
    return render_template(
        template_name_or_list='logs.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) }
    )


if __name__ == "__main__":
    # run in development environment only, no external access possible (safe)
    app.run(debug=True, use_reloader=False)
    # run on all IP addresses, external access allowed (unsafe)
    # app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
