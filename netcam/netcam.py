# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

from flask import Flask
from flask import render_template
from flask import make_response
from flask import stream_with_context
from flask import url_for
from flask import Response
from flask import session
import cv2
from cameras import config
import logging
import sys
import uuid
from threading import current_thread
import streaming

stream = streaming.Streaming()

app = Flask(__name__)

# -----------------------------------------------------------
def set_streaming_context(streaming=False):
    """
    read cookies from the application config
    call this at the beginning of the request
    set streaming = True for all streaming routes
    """
    global stream
    thread = current_thread().getName()
    if 'userid' in session:
        userid = session
    else:
        # new session, add synthetic user ID
        userid = uuid.uuid4().hex # unique, 32 chars
        session['userid'] = userid
    success = stream.set_context(userid, streaming)
    return userid, thread

# -----------------------------------------------------------
@app.route("/")
@app.route("/home")
def home():
    """ top level webpage """
    template='home.html'
    idx=0 # [default] first camera
    usrd, thrd = set_streaming_context(streaming=True)
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "hamburger",
                "url": url_for("menu_main", _external=True)},
            context={
                "template": template,
                "index": str(idx)}
    ))
    return rsp

@app.route("/video_feed/<template>/<idx>")
def video_feed(template, idx):
    """ top level streaming page, referenced by home.html template """
    userid = session['userid']
    return Response(
        stream_with_context(generate_frames(userid, template, idx)),
        mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames(userid, template, idx):
    """ get synced frame from cameras[idx] (blocking) """
    global stream
    logging.debug('>>> Start streaming loop for user '+userid)
    while stream.is_allowed(userid):
        # get frame converted to low resolution jpeg (smooth html video viewing)
        frame = thrds[int(idx)].get_frame_picture(width=960)
        retval, buffer = cv2.imencode('.jpg', frame)
        # stream to template to browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    # end of while loop
    logging.debug('<<< Stop streaming loop for user ' + userid)

@app.route("/heartbeat/<userid>")
def heartbeat(userid):
    """ check if user has dropped the browser connection to top level """
    pass # todo define actions here

# -----------------------------------------------------------
@app.route("/menu/main")
def menu_main():
    template = 'menu.main.html'
    usrd, thrd = set_streaming_context()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

# -----------------------------------------------------------
@app.route("/tiles")
def tiles():
    template = 'tiles.html'
    usrd, thrd = set_streaming_context()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

# -----------------------------------------------------------
@app.route("/menu/clips")
def menu_clips():
    template = 'menu.clips.html'
    usrd, thrd = set_streaming_context()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

# -----------------------------------------------------------
@app.route("/clips/<period>")
def clips(period):
    template = 'clips.html'
    usrd, thrd = set_streaming_context()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            period=period,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

# -----------------------------------------------------------
@app.route("/clip/<clipdate>/<cliptime>")
def clip(clipdate, cliptime):
    """
    render the videoclip defined by clipdate and cliptime
    :param clipdate: string, format: yyyy-mm-dd
    :param cliptime: string, format: hh:mm:ss.mmm
    :return: template rendered with information
    """
    template = 'clip.html'
    usrd, thrd = set_streaming_context()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

# -----------------------------------------------------------
@app.route("/states")
def states():
    template = 'states.html'
    usrd, thrd = set_streaming_context()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

# -----------------------------------------------------------
@app.route("/logs")
@app.route("/logs/<index>")
def logs(index=''):
    template = 'logs.html'
    usrd, thrd = set_streaming_context()
    log_items = get_log_items(index)
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)},
            logs=log_items
        ))
    return rsp

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

# ===========================================================
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
    # get confidential information
    cnfg = config.Config()
    # setup logging formats (depends on environments)
    myfmt = '%(asctime)s | %(levelname)s | %(threadName)s | %(module)s | %(message)s'
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
    # setup logging -----
    cnfg = setup_logging()
    logging.info(">>> Start Flask application '"+app.name+"'")

    # setup session variable
    app.secret_key = cnfg.get_flask_secret()

    # setup all threads needed for the application -----
    thrds = setup_threads(cnfg)

    # run Flask server -----
    if cnfg.is_debug_mode():
        # [safe] run Flask webserver in development environment only, no external access possible (safe)
        # app.run(debug=True, use_debugger=False, use_reloader=False) # or comment + uncomment the last line of code

        # [unsafe] run on all IP addresses, external access allowed
        app.run(debug=True, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        # run in production mode
        app.run(debug=False, use_debugger=False, use_reloader=False)

    # stop and kill threads -----
    for thrd in thrds:
        thrd.terminate_thread()
        thrd.join()
    # finished log message
    logging.info("<<< Stop Flask application '"+app.name+"'")
