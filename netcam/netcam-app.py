# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
import os.path

# Flask webpage for displaying online and offline videos.
# - Based upon some cheap ANNKE IP cameras (AN-I91BL0102),
#   which have two video streams: main(8MP) and sub(640x480).
# This Flask App uses long-running-child-processes (netcam-recorder.py)
# - managed with: tbd
# - IPC with:     tbd

from flask import Flask
from flask import render_template
from flask import make_response
from flask import stream_with_context
from flask import url_for
from flask import Response
from flask import session
from flask import request
from flask import send_file
from cameras import config
from logger import tcpserver
import threading
from threading import current_thread
from multiprocessing.connection import Client
import cv2
import sys
import uuid
import subprocess
from netcam.database import database
from datetime import datetime
import json

# FLASK CODE SECTION ===================================================

app = Flask(__name__)

# CONSTANT DECLARATIONS:

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

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
        try:
            success, frame = stream.read() # read one frame 640 x 480
            if success and frame is not None:
                retval, buffer = cv2.imencode('.jpg', frame)
                # stream to template and user's browser
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except cv2.error:
            app.logger.error("Cannot connect to camera "+idx)
            break
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
@app.route("/clips")
@app.route("/clips/<index>")
def clips(index=''):
    template = 'clips.html'
    infos = get_infos(index)
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)},
            attributes={
                "date": index,
                "infos": infos
            }
        ))
    return rsp

def get_weekday(dtstrng):
    """ convert date string to the weekday: Monday, Tuesday, etc. """
    date_object = datetime.strptime(dtstrng, "%Y-%m-%d")
    day_of_week = date_object.weekday() # integer: where 0 is Monday
    return WEEKDAYS[day_of_week]

def get_infos(day):
    """ get the infos for video clips """
    infs = []
    db = database.Database()
    if day == '' or day is None:
        rows = db.get_clips_per_day()
        for row in rows:
            key = row[0]
            ymd = key[0:4]+'-'+key[4:6]+'-'+key[6:8]
            wkdy = get_weekday(ymd)
            cnt = str(row[1])
            infs.append((key, wkdy, ymd, cnt)) # tuple: key(hidden), weekday, date string, counter
        return infs
    else:
        # get the infos of all videoclips for day
        rows = db.get_clips_for_day(day)
        for row in rows:
            fname = row[0] # filename
            idx = row[1] # idx
            key = row[2] # ymdhms
            tod = key[8:10]+':'+key[10:12]+':'+key[12:]
            inf = row[3]
            dctny = json.loads(inf.replace("'", '"'))
            qa = dctny['qa']
            frms = dctny['frms']
            infs.append((key, tod, str(frms), str(idx) )) # tuple: key(hidden), time of day, no of frames, camera number
        return infs

# -----------------------------------------------------------
@app.route("/clip")
@app.route("/clip/<key>")
@app.route("/clip/<key>/<action>")
def clip(key='', action=''):
    """
    render the videoclip defined by the clip date time
    :param key: string, format: yyyymmddhhmmss
    :return: template rendered with information
    """
    mode = 'jpg'
    current_key = key
    db = database.Database()
    if action == "previous":
        current_key = db.get_previous_clip_index(key)
        pass
    elif action == "next":
        current_key = db.get_next_clip_index(key)
        pass
    elif action == "play":
        mode = 'avi'
    #
    template = 'clip.html'
    rsp = make_response(
        render_template(
            template_name_or_list=template,
            key=current_key,
            mode=mode,
            navigation={
                "icon": "cross",
                "url": url_for("home", _external=True)}
        ))
    return rsp

@app.route("/picture_feed/<key>")
def picture_feed(key):
    """ display picture 'key' on web client """
    imgpath = get_image_path(key, type=".jpg")
    return send_file(imgpath, mimetype='image/jpg')

@app.route("/clip_feed/<key>")
def clip_feed(key):
    """ display video file """
    return Response(
        stream_with_context(generate_clips(key)),
        mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_clips(key):
    """ get frames from local video file """
    imgpath = get_image_path(key, type=".avi")
    vcap = cv2.VideoCapture(imgpath)
    while vcap.isOpened():
        try:
            success, frame = vcap.read() # read one frame
            if success and frame is not None:
                rframe = cv2.resize(frame, (1920, 1080)) # use HD resolution for web
                retval, buffer = cv2.imencode('.jpg', rframe)
                # stream to template and user's browser
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except cv2.error:
            app.logger.error("Cannot connect/open file "+imgpath)
            break
    vcap.release()
    return

def get_image_path(key, type=".avi"):
    """ get the path to the image which is associated with key """
    db = database.Database()
    dict = db.get_clip(key)
    avi= dict[0][0]
    if type == ".avi":
        if os.path.isfile(avi):
            return avi
        else:
            return app.root_path + "/static/lightning.jpg"
    else:
        jpg = avi.replace(".avi", type)
        if os.path.isfile(jpg):
            return jpg
        else:
            return app.root_path+"/static/lightning.jpg"

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
    """
    get information from ipc server (camera port):
    - open connection
    - send request
    - receive information
    - close connection
    """
    address = ('localhost', cnfg.get_ipc_port(idx))
    try:
        with Client(address, authkey=cnfg.get_ipc_authkey()) as conn:
            conn.send('information?') # information request
            info = conn.recv() # wait for information response
            if type(info) is dict:
                return info
            else:
                app.logger.error('IPC response error: '+str(info))
                return {"cnnprbl": True}
    except Exception as exc:
        # Connection refused [Errno 61]
        return {"cnnprbl": True}

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

# MAIN CODE SECTION ===========================================================

def get_process_infos(key):
    """ get name + index of each netcam-recorder.py application running as a process """
    subp = subprocess.Popen(["ps -ax | grep "+key], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    subc = subp.communicate() # get stdout and stderr
    stdout = subc[0].decode("utf-8") # stdout to string
    idxs = [] # return value
    for line in stdout.splitlines():
        chnks = line.split()
        idx = chnks[-1] # camera index
        cmd = chnks[-2] # command with scriptname
        if idx.isnumeric() and key in cmd:
            idxs.append(int(idx))
    return idxs

def start_long_running_processes(cnfg):
    """ setup long-running processes (netcam-recorder.py) """
    ips = cnfg.get_ip_address_list()
    pexe = "/Users/mart/Projects/netcam-git/venv/bin/python3.9"  # [default] macbook dev environment
    papp = "netcam-recorder.py" # [default] subprocess name
    keys = get_process_infos(papp) # indexes of running netcan-recorder processes
    for idx, ip in enumerate(ips):
        if idx not in keys:
            try:
                # start python netcam-recorder.py script
                p = subprocess.Popen(
                    [pexe, papp, str(idx)],
                    stdin=subprocess.DEVNULL,
                    stdout=open('netcam.log', 'w'),
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    shell=False)
                app.logger.info("Started new subprocess "+papp+" "+str(idx))
            except subprocess.CalledProcessError as e:
                app.logger.error("Cannot start new subprocess "+papp+" "+str(idx))
        else:
            app.logger.info("Continue using subprocess "+papp+" "+str(idx))
    pass

def start_threads():
    """ setup all threads needed for this app """
    thrds = []
    # setup common logger thread
    lggr = tcpserver.Tcpserver()
    lggr.daemon = True
    lggr.start()
    thrds.append(lggr)
    #
    return thrds

def kill_threads(thrds):
    """ kill all threads running in this app """
    for thrd in thrds:
        thrd.terminate_thread()
        thrd.join()
    pass

if __name__ == "__main__":
    """ initialize the netcam Flask application """

    # setup configuration and logging -----
    cnfg = config.Config()
    cnfg.set_logging()
    app.logger.info(">>> Start Flask application '"+app.name+"'")
    errors = cnfg.get_error_messages()
    if len(errors) >0:
        for msg in errors:
            app.logger.error(msg)
        app.logger.error('Configuration error in file .ENV, please fix.')
        sys.exit(1)

    # [debug] wz = logging.getLogger('werkzeug')
    # [debug] wz.setLevel(logging.WARNING)

    # setup session variable
    app.secret_key = cnfg.get_flask_secret()

    # start all threads needed in this application -----
    thrds = start_threads()

    # start all processes needed for the application -----
    start_long_running_processes(cnfg)

    # run Flask server -----
    if cnfg.is_debug_mode():
        # [safe] run Flask webserver in development environment only, no external access possible (safe)
        # app.run(debug=True, use_debugger=False, use_reloader=False) # or comment + uncomment the last line of code

        # [unsafe] run on all IP addresses, external access allowed
        app.run(debug=False, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)
    else:
        # run in production mode
        app.run(debug=False, use_debugger=False, use_reloader=False)

    # kill threads -----
    kill_threads(thrds)

    # finish app
    app.logger.info("<<< Stop Flask application '"+app.name+"'")
    sys.exit()
