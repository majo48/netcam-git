# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
import threading

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

app = Flask(__name__)

# -----------------------------------------------------------
@app.route("/")
@app.route("/home")
def home():
    """ top level webpage """
    template='home.html'
    idx=0 # [default] first camera
    if 'userid' not in session:
        session['userid'] = uuid.uuid4().hex # unique, 32 chars
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
    thread = current_thread().getName()
    logging.debug('>>> Start streaming loop for user '+userid+' and '+thread)
    while True:
        # get frame converted to low resolution jpeg (smooth html video viewing)
        frame = thrds[int(idx)].get_frame_picture(width=960)
        retval, buffer = cv2.imencode('.jpg', frame)
        # stream to template to browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    # end of while loop
    logging.debug('<<< Stop streaming loop for user ' + userid+' and '+thread)

@app.route("/heartbeat/<userid>")
def heartbeat(userid):
    """ check if user has dropped the browser connection to top level """
    logging.debug('Request to route /heartbeat ('+current_thread().getName()+')')
    pass # todo define actions here

# -----------------------------------------------------------
@app.route("/menu/main")
def menu_main():
    """ main menu for all pages excluding /home """
    template = 'menu.main.html'
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
    """ display states page """
    logging.debug('Request to route /states ('+current_thread().getName()+')')
    template = 'states.html'
    state_items = get_state_items()
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)},
            states = state_items
        ))
    return rsp

def get_state_items():
    """ simple display of some state items """
    state_items = []
    state_items.append('THREADS')
    state_items.append('Current thread: '+current_thread().getName())
    threads = threading.enumerate()
    for thread in threads:
        gtp = get_thread_position(thread)
        state_items.append(gtp)
    return state_items

def get_thread_position(thread):
    """
    get active threads, current filename, code section with line number
    note: sys._current_frames() is a non-public class methode (see internet)
    """
    frame = sys._current_frames().get(thread.ident, None)
    if frame:
        dict = {
            "threadname": thread.name,
            "daemon": str(thread.daemon),
            "filename": frame.f_code.co_filename,
            "codesection": frame.f_code.co_name,
            "codeline": str(frame.f_code.co_firstlineno) }
        strng = ''
        for key, val in dict.items():
            strng += key + ": " + val + ", "
        return strng[:-2]

# -----------------------------------------------------------
@app.route("/logs")
@app.route("/logs/<index>")
def logs(index=''):
    """ display logs page """
    logging.debug('Request to route /logs ('+current_thread().getName()+')')
    template = 'logs.html'
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
    fltr = index.upper()
    fp = open(cnfg.get_log_filename())
    while True:
        item = fp.readline()
        if len(item) == 0:
            break
        if (index != '') and (index != 'all'):
            if item.find(fltr) != -1:
                log_items.append(item) # filtered item
        else:
            log_items.append(item) # unfiltered item
    if len(log_items) == 0:
        log_items.append('No log items available.')
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
        app.run(debug=False, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        # run in production mode
        app.run(debug=False, use_debugger=False, use_reloader=False)

    # stop and kill threads -----
    for thrd in thrds:
        thrd.terminate_thread()
        thrd.join()
    # finished log message
    logging.info("<<< Stop Flask application '"+app.name+"'")
