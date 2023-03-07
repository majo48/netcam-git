# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

# Long-running-child-process for recording video motions.
# This process has no bindings with the Flask application
# other than ipc communication commands:
#     'information?' request for information from the camera
#     'terminate!'   request for termination of the recording process
# and logging events to disk files (.log and .avi).

from threading import Thread
from threading import Event
from cameras import config
from cameras import videoclip
from cameras import motion
from cameras import camera, frame
import logging
import argparse
from multiprocessing.connection import Listener

def _get_camera_info():
    """ get camera infos for ipc server """
    cam = thrds[0] # camera always first thread
    info = {"cam_idx": recorder_index,
            "cam_fps": cam.get_fps(),
            "frm_cnt": cam.get_frame_count(),
            "frm_skp": cam.get_skipped_count(),
            "cnnprbl": cam.has_connection_problem()}
    return info

def run_ipc_server():
    """ inter process communication """
    terminate_origin = 'n/a'
    address = ('localhost', cnfg.get_ipc_port(recorder_index))  # AF_INET - TCP socket
    listener = Listener(address, authkey=cnfg.get_ipc_authkey())
    try:
        conn = listener.accept()
        logging.debug('>>>> IPC connection accepted from ', listener.last_accepted)
        while True:
            msg = conn.recv()
            # do something with msg
            if msg == 'terminate!':
                conn.send('OK')
                terminate_origin = 'ipc'
                # close connection and kill all threads in this app
                conn.close()
                break
            elif msg == 'information?':
                # provide camera information for the Flask app
                conn.send(_get_camera_info()) # send to Flask application
            else:
                logging.error('IPC received illegal verb: '+msg)
                conn.send('Unknown verb: '+msg) # send to Flask application
            pass
    except KeyboardInterrupt:
        terminate_origin = 'keyboard'
    finally:
        # terminate IPC
        logging.debug('<<<< IPC connection closed (terminate command received from '+terminate_origin+').')
        listener.close()

def parse_cli():
    """ parse the commandline: python3 netcam-recorder.py idx """
    parser = argparse.ArgumentParser(
        description="Start video recordings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("idx", help="Camera index (0..n).")
    args = parser.parse_args()
    cli = vars(args)
    ridx = int(cli["idx"])
    if not (0 <= ridx <= cnfg.get_max_camera_index()):
        raise ValueError('recorder_index out of bounds: '+str(ridx))
    return ridx

def setup_threads(cnfg, idx):
    """ setup all threads needed for this app """
    thrds = []
    frm = frame.Frame(None)
    url = cnfg.get_rtsp_url(idx)
    ip = cnfg.get_ip_address(idx)

    # camera thread, connected to videoclip through frm, always thrds[0]
    cam = camera.Camera(idx, ip, url, frm)  # instantiate a camera feed
    cam.daemon = True
    cam.start()
    thrds.append(cam)

    # videoclip threads, connected to camera only
    nfps = cnfg.get_nominal_fps(idx)
    roi = cnfg.get_roi(idx)
    mtn = motion.Motion(roi)
    clp = videoclip.VideoClip(idx, nfps, cam, mtn) # instantiate video clip maker
    clp.daemon = True
    clp.start()
    thrds.append(clp)
    #
    return thrds


if __name__ == "__main__":
    """ initialize the netcam app """
    cnfg = config.Config() # get common configuration information
    cnfg.set_logging() # setup logging configuration

    # parse commandline -----
    recorder_index = parse_cli()
    logging.info(">>> Start recorder application no. "+str(recorder_index))

    # build all threads: camera and videoclip -----
    thrds = setup_threads(cnfg, recorder_index)

    # run ipc server (in main thread) -----
    run_ipc_server()

    # kill threads -----
    for thrd in thrds:
        thrd.terminate_thread()
        thrd.join()

    # finished, log message -----
    logging.info("<<< Stopped recorder application no. " + str(recorder_index))
    pass
