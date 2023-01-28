# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

from flask import Flask
from flask import render_template
from flask import url_for
from flask import Response
import cv2
import imutils
from cameras import config
import logging
import sys


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
    """ get synced frame from cameras[idx] (blocking) """
    while True:
        # todo: add heartbeat test in order to avoid permanent threads
        # convert frame to low resolution jpeg (smooth html video viewing)
        frame = thrds[int(idx)].get_frame_picture(width=960)
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
@app.route("/logs/<index>")
def logs(index=''):
    log_items = get_log_items(index)
    return render_template(
        template_name_or_list='logs.html',
        navigation={
            "icon": "cross",
            "url": url_for("home", _external=True) },
        logs=log_items
    )

def get_log_items(index):
    """ get filtered logs """
    log_items = []
    fp = open(cnfg.get_log_filename())
    while True:
        item = fp.readline()
        if len(item) == 0:
            break
        log_items.append(item)
    return log_items

def setup_threads(cnfg):
    """ setup all threads needed for this app """
    ips = cnfg.get_ip_adresse_list()
    from cameras import camera, frame
    cams = []
    for idx, ip in enumerate(ips):
        frm = frame.Frame(None)
        url = cnfg.get_rtsp_url(idx)
        cam = camera.Camera(idx,url,frm) # instantiate a camera feed
        cam.daemon = True # define feed as daemon thread
        cam.start() # start daemon camera thread
        cams.append(cam)
    return cams

def setup_logging():
    """ setup logging for development and production environments """
    myfmt = '%(asctime)s | %(levelname)s | %(threadName)s | %(module)s | %(message)s'
    cnfg = config.Config()
    if cnfg.is_debug_mode():
        # basic configuration for development environment
        logging.basicConfig(
            format=myfmt,
            filename=cnfg.get_log_filename(),
            filemode='w',
            encoding='utf-8',
            level='DEBUG')
        # also send logs to the console
        lggr = logging.getLogger()
        lggr.setLevel(logging.DEBUG)
        hndlr = logging.StreamHandler(sys.stdout)
        hndlr.setLevel(logging.DEBUG)
        hndlr.setFormatter(logging.Formatter(myfmt))
        lggr.addHandler(hndlr)
    else:
        # basic configuration for production environment
        logging.basicConfig(
            format=myfmt,
            filename=cnfg.get_log_filename(),
            filemode='a',
            encoding='utf-8',
            level='INFO')
    return cnfg


if __name__ == "__main__":
    """ initialize the netcam app """
    # setup logging
    cnfg = setup_logging()
    logging.info(">>> Start Flask application '"+app.name+"'")

    # setup all threads needed for the application
    thrds = setup_threads(cnfg)

    # run Flask server
    if cnfg.is_debug_mode():
        # [safe] run Flask webserver in development environment only, no external access possible (safe)
        # app.run(debug=True, use_debugger=False, use_reloader=False) # or comment + uncomment the last line of code

        # [unsafe] run on all IP addresses, external access allowed
        app.run(debug=True, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        # run in production mode
        app.run(debug=False, use_debugger=False, use_reloader=False)

    # stop and kill threads
    for thrd in thrds:
        thrd.terminate_thread()
        thrd.join()
    # finished log message
    logging.info("<<< Stop Flask application '"+app.name+"'")
