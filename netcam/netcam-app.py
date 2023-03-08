# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

# Flask webpage for displaying online and offline videos.
# - Based upon some cheap ANNKE IP cameras (AN-I91BL0102),
#   which have two video streams: main(8MP) and sub(640x480).
# This Flask App uses long-running-child-processes (netcam-recorder.py)
# - managed with: tbd
# - IPC with:     tbd

import threading
from flask import Flask
from flask import render_template
from flask import make_response
from flask import stream_with_context
from flask import url_for
from flask import Response
from flask import session
from flask import request
from cameras import config
from cameras import videoclip
from cameras import motion
from cameras import camera, frame
from threading import current_thread
from multiprocessing.connection import Client
import cv2
import logging
import sys
import uuid

app = Flask(__name__)

# -----------------------------------------------------------
@app.route("/")
@app.route("/home")
def home():
    """ top level webpage """
    idx = _get_camera_index()
    if 'userid' not in session:
        session['userid'] = uuid.uuid4().hex # unique, 32 chars
    info = get_camera_info(idx)
    connection_problem = info.get('cnnprbl')
    template='home.html'
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "hamburger",
                "url": url_for("menu_main", _external=True)},
            context={
                "index": str(idx),
                "connection_problem": connection_problem}
    ))
    return rsp

def _get_camera_index():
    """
    get the camera index fom the request
    :return int
    """
    args = request.args
    if 'camera' in args:
        idx = int(args['camera'])
    else:
        idx=0 # [default] first camera
    if 'next' in args:
        next = args['next']
        if next in ["left", "right"]:
            if next == 'left':
                ndx = idx-1
            else:
                ndx = idx+1
            idx = ndx # set index to next index
    return get_bounded_camera_index(idx)

def get_bounded_camera_index(ndx):
    """ keep the camera index inside bounds 0..last camera in config """
    idx = ndx
    max_idx = cnfg.get_max_camera_index()
    if ndx < 0:
        idx = 0
    elif ndx > max_idx:
       idx = max_idx
    return idx

# -----------------------------------------------------------
@app.route("/video_feed/<idx>/<concurrent>")
def video_feed(idx, concurrent):
    """ top level streaming page, referenced by home.html template """
    userid = session['userid']
    return Response(
        stream_with_context(generate_frames(userid, idx, int(concurrent))),
        mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames(userid, idx, concurrent):
    """ get synced frame from cameras[idx] (blocking) """
    rtsp_url = cnfg.get_rtsp_url(int(idx), stream='sub')  # 640 x 480 pixel substream
    stream = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = stream.read() # read one frame 640 x 480
        if success and frame is not None:
            retval, buffer = cv2.imencode('.jpg', frame)
            # stream to template and user's browser
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    pass # managed by Flask

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
    indices = [] # index list, one for each camera
    for x in range(len(cnfg.get_ip_address_list())):
        indices.append(str(x))
    conc = len(indices) # number of concurrent cameras
    # calculate the width or each camera display
    concwidth = 100.0
    if 2<= conc <= 4: concwidth = 49.8 # two columns
    elif 5 <= conc <= 9: concwidth = 33.1 # three columns
    # build response (using template)
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)},
            indices=indices,
            concurrent=str(conc),
            widthpercent=concwidth
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
    # get thread info -----
    state_items.append('THREADS')
    state_items.append('Current thread: '+current_thread().getName())
    threads = threading.enumerate()
    for thread in threads:
        gtp = get_thread_position(thread)
        state_items.append(gtp)
    # get camera info -----
    state_items.append(('CAMERAS')) # print header
    for idx in range(len(cnfg.get_ip_address_list())):
        info = get_camera_info(idx)
        state_items.append(
            'Camera: '+str(idx)+
            ', frames per second: '+str(info.get('cam_fps'))+
            ', frames: '+str(info.get('frm_cnt'))+
            ', skipped: '+str(info.get('frm_skp'))
        )
    # exit -----
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
            "codeline": str(frame.f_lineno) }
        strng = ''
        for key, val in dict.items():
            strng += key + ": " + val + ", "
        return strng[:-2]

def get_camera_info(idx):
    """ get information from ipc server (camera) """
    address = ('localhost', cnfg.get_ipc_port(idx))
    with Client(address, authkey=cnfg.get_ipc_authkey()) as conn:
        conn.send('information?') # information request
        info = conn.recv() # wait for information response
        if type(info) is dict:
            return info
        else:
            logging.error('IPC response error: '+str(info))
            return {} # empty container

# -----------------------------------------------------------
@app.route("/logs")
@app.route("/logs/<index>")
def logs(index=''):
    """ display logs page """
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

def setup_long_running_processes(cnfg):
    """ setup long-running processes (netcam-recorder.py) """
    ips = cnfg.get_ip_address_list()
    for idx, ip in enumerate(ips):
        pass
        # todo initialize recorder processes here
    pass

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
    setup_long_running_processes(cnfg)

    # run Flask server -----
    if cnfg.is_debug_mode():
        # [safe] run Flask webserver in development environment only, no external access possible (safe)
        # app.run(debug=True, use_debugger=False, use_reloader=False) # or comment + uncomment the last line of code

        # [unsafe] run on all IP addresses, external access allowed
        app.run(debug=False, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        # run in production mode
        app.run(debug=False, use_debugger=False, use_reloader=False)

    # stop and kill processes -----
    for idx in range(len(cnfg.get_ip_address_list())):
        pass # todo kill ipc processes here

    # finished log message
    logging.info("<<< Stop Flask application '"+app.name+"'")
