# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

from flask import Flask
from flask import render_template
from flask import url_for
from flask import Response
import cv2
import imutils
from cameras import config


app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    idx=0 # default, first camera
    return render_template(
        template_name_or_list='home.html',
        navigation={
            "icon": "hamburger",
            "url": url_for("menu_main", _external=True) },
        index={
            "current": str(idx),
            "max": str(len(thrds)) }
    )

@app.route("/video_feed/<idx>")
def video_feed(idx):
    return Response(
        generate_frames(idx),
        mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames(idx):
    """
    get synced frame from cameras[idx] (blocking)
    note#1: width=810 accounts for 56% CPU load on macbook.local
    note#2: background, w.o. display of video_stream, accounts for 7.3% CPU load
    todo: improve efficiency of video streaming to web browsers by >50%
    """
    while True:
        # count = thrds[int(idx)].get_frame_count()
        # convert frame to low resolution jpeg (smooth html video viewing)
        frame = imutils.resize(thrds[int(idx)].get_frame(), width=810)
        retval, buffer = cv2.imencode('.jpg', frame)
        # stream to template to browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

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

def setup_threads():
    """ setup all threads needed for this app """
    from cameras import config
    conf = config.Config()
    ips = conf.get_ip_adresse_list()
    from cameras import camera
    cams = []
    for idx, ip in enumerate(ips):
        url = conf.get_rtsp_url(idx)
        cam = camera.Camera(idx,url)
        cam.daemon = True
        cam.start()
        cams.append(cam)
    return conf, cams


if __name__ == "__main__":
    """ initialize the netcam app """
    # setup all threads needed for the application
    conf, thrds = setup_threads()

    if conf.is_debug_mode():
        # [safe] run Flask webserver in development environment only, no external access possible (safe)
        app.run(debug=True, use_debugger=False, use_reloader=False) # or comment + uncomment the last line of code

        # [unsafe] run on all IP addresses, external access allowed
        # app.run(debug=True, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        # run in production mode
        app.run(debug=False, use_debugger=False, use_reloader=False)

    # stop and kill threads
    for thrd in thrds:
        thrd.terminate_thread()
        thrd.join()
