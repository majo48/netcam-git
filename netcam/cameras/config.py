# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# config class modul for retrieving non-public information, e.g. may contain some credentials you do not want to share.

import logging
import sys
import os
from dotenv import load_dotenv
import platform
import json
from datetime import datetime
import subprocess
import shutil

class Config:
    """
    This is place to define the hardware and software configuration parameters for accessing the network cameras.
    The cameras have common usernames and passwords for accessing the video information, however the IP addresses
    are unique; one IP for each camera (fixed IP addresses).
    - Confidential information is kept in the .env file (root or user folder)
    - Hardware information will define the DEBUG_MODE: True or False
    - Other information can be defined as constants in this config.py file
    """
    DRIVE_LABEL = 'WD_Elements'  # [default] case-sensitive
    DEVELOPMENT_PATH = '/Users/mart/projects/netcam-git/netcam/' # [default]
    PRODUCTION_PATH = '/var/netcam/' # [default]
    LOG_FILE_NAME = 'logs/netcam.?.log' # '[default]
    VIDEO_FILE_NAME = 'videos/recorder.?1.time.?2.avi' # [default]

    def __init__(self):
        """ initialize an instance of the class """
        load_dotenv()
        # set confidential info
        self._flask_secret = os.getenv('FLASK_SECRET')

        # get config list from .env
        self._config = []
        for cnt in range(10):
            tpl = os.getenv('FLASK_CAM'+str(cnt))
            if tpl is not None:
                jsn = json.loads(tpl)
                self._config.append(jsn)

        # check config list for inconsistencies
        self.msgs = [] # error messages
        for idx in range(len(self._config)):
            if "ttl" not in self._config[idx]: self.msgs.append("Missing 'ttl' in .ENV FLASK_CAM" + str(idx))
            if "usr" not in self._config[idx]: self.msgs.append("Missing 'usr' in .ENV FLASK_CAM" + str(idx))
            if "pw" not in self._config[idx]: self.msgs.append("Missing 'pw' in .ENV FLASK_CAM" + str(idx))
            if "ip" not in self._config[idx]: self.msgs.append("Missing 'ip' in .ENV FLASK_CAM" + str(idx))
            if "fps" not in self._config[idx]: self.msgs.append("Missing 'fps' in .ENV FLASK_CAM" + str(idx))
            if "roi" not in self._config[idx]: self.msgs.append("Missing 'roi' in .ENV FLASK_CAM" + str(idx))
        self._max_camera_index = len(self._config)-1

        # set predefined tcp ports for each ipc server (cameras) and flask ipc client
        self._ipc_port_flask = int(os.getenv('FLASK_IPC_PORT'))
        prt = int(os.getenv('FLASK_IPC_CAMS'))
        self._ipc_ports = []
        for idx in range(len(self._config)):
            self._ipc_ports.append(prt)
            prt += 1

        # set common IPC secret
        s = os.getenv('FLASK_IPC_SECRET')
        self._ipc_authkey = s.encode('ascii') # bytes

        # set debug_mode info
        mynode = platform.uname().node
        self._debug_mode = (mynode == 'macbook.local' or mynode == 'nvr')

        # check for external disk (already mounted by admin!)
        self._mount_point = self.check_external_disk(self.DRIVE_LABEL)
        if self._mount_point is not None:
            contents = self.read_external_disk(self._mount_point)
            if 'netcam' not in contents:
                self.make_standard_folders(self._mount_point)
        pass

    def get_ipc_port(self, idx):
        """ get the ipc port reserved for camera idx """
        if 0 <= idx < len(self._config):
            return self._ipc_ports[idx]
        else:
            return None

    def get_ipc_port_flask(self):
        """ get the ipc port reserved for the flask app """
        return self._ipc_port_flask

    def get_ipc_authkey(self):
        """ get the ipc authentication key """
        return self._ipc_authkey

    def get_max_camera_index(self):
        """ get the maximum index for cameras, minimum = 0 """
        return self._max_camera_index

    def get_title(self, idx):
        """ get the title of camera 'idx'  """
        if 0 <= idx < len(self._config):
            return self._config[idx]['ttl']
        else:
            return None

    def get_username(self, idx):
        """ get the username for accessing camera 'idx' """
        if 0 <= idx < len(self._config):
            return self._config[idx]['usr']
        else:
            return None

    def get_password(self, idx):
        """ get the password for accessing the camera 'idx' """
        if 0 <= idx < len(self._config):
            return self._config[idx]['pw']
        else:
            return None

    def get_ip_address(self, idx):
        """ get the ip address of camera 'idx' """
        if 0 <= idx < len(self._config):
            return self._config[idx]['ip']
        else:
            return None

    def get_nominal_fps(self, idx):
        """ get the nominal fps for camera 'idx' """
        if 0 <= idx < len(self._config):
            return self._config[idx]['fps']
        else:
            return None

    def get_roi(self, idx):
        """ get the region of interest (x,y,w,h) for camera 'idx' """
        if 0 <= idx < len(self._config):
            roi = self._config[idx]['roi']
            return eval(roi) # tuple: (x, y, w, h)
        else:
            return None

    def get_ip_address_list(self):
        """ get the list of IP addresses of the network cameras """
        ips = []
        for idx in range(len(self._config)):
            ips.append(self._config[idx]['ip'])
        return ips

    def get_rtsp_url(self, idx, stream='main'):
        """
        get the rtsp url for indexed camera device, zero based index
        Some variants, which work:
        "rtsp://<user>:<password>@<ip>:554/H264/ch1/main/av_stream" [default]
        "rtsp://<user>:<password>@<ip>:554/H264/ch1/sub/av_stream" [low resolution 640 x 480]
        "rtsp://<user>:<password>@<ip>:554/H264/ch2/main/av_stream" [same as default]
        "rtsp://<user>:<password>@<ip>:554/Streaming/Channels/101?transport-mode=unicast&profile=Profile_1" [same as default]
        """
        ip = self.get_ip_address(idx)
        if isinstance(ip, int): # integer
            return ip # webcam index
        elif isinstance(ip, str):
            # ip address string, like '192.168.1.22'
            url = "rtsp://<user>:<password>@<ip>:554/H264/ch1/<stream>/av_stream"
            url = url.replace('<user>', self.get_username(idx))
            url = url.replace('<password>', self.get_password(idx))
            url = url.replace('<ip>', ip) # ip address string
            url = url.replace('<stream>', stream)
            return url
        else:
            raise TypeError('IP address should be an integer or string.')

    def set_logging(self):
        """
        setup logging for development and production environments
        this is common for all netcam apps (connected through sockets)
        """
        myfmt = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        # setup logging formats (depends on environments)
        if self.is_debug_mode():
            # basic configuration for development environment
            logging.basicConfig(
                format=myfmt,
                filename=self.get_log_filename(),
                filemode='w',
                encoding='utf-8',
                level='DEBUG')
            # also send logs to the console
            lggr = logging.getLogger()
            lggr.setLevel(logging.DEBUG) # [default] development
            hndlr = logging.StreamHandler(sys.stdout)
            hndlr.setLevel(logging.DEBUG)
            hndlr.setFormatter(logging.Formatter(myfmt))
            lggr.addHandler(hndlr)
        else:
            # basic configuration for production environment
            logging.basicConfig(
                format=myfmt,
                filename=self.get_log_filename(),
                filemode='a',
                encoding='utf-8',
                level='INFO') # [default] production
        pass

    def is_debug_mode(self):
        """ get DEBUG_MODE variable """
        return self._debug_mode

    def is_production_mode(self):
        """ get inverted DEBUG_MODE variable """
        return not self.is_debug_mode()

    def check_external_disk(self, drive_label):
        """
        check if drive(DRIVE_LABEL or Volume Name) is connected
        if True: return mount point
        """
        try:
            # check if external disk is connected
            output = subprocess.check_output(['mount'])
            output = output.decode("utf-8")
            lines = output.split("\n")
            for line in lines:
                if drive_label in line:
                    device_node = line.split()[0]  # Device Node, last part: device id
                    mount_point = line.split()[2]  # Mount Point
                    return mount_point
        except BaseException as err:
            pass
        return None

    def read_external_disk(self, mount_point):
        # read files & folders in the mount point
        try:
            contents = os.listdir(mount_point)
            return contents
        except BaseException as err:
            pass
        return None

    def make_standard_folders(self, mount_point):
        """ mkdir netcam, netcam/logs and /netcam/videos """
        folders = ['netcam', 'netcam/logs', 'netcam/videos']
        try:
            for folder in folders:
                path = os.path.join(mount_point, folder)
                os.mkdir(path)
            #
            return True
        except BaseException as err:
            pass
        return False

    def check_disk_capacity(self, mount_point):
        """ get drive capacity """
        stats = shutil.disk_usage(mount_point)
        hrgb = []
        for stat in stats:
            hrgb.append(round(stat / 1000000000, 2))  # GB
            pass
        return hrgb  # list: total, used, free in GigaBytes

    def get_standard_path(self):
        """
            get the path for the 'netcam' folder, for wring to netcam/logs and netcam/videos
            1. The external drive always has precedence over the local drive.
            2. The external drive must be mounted prior to usage by this app.
        """
        if self._mount_point is not None:
            return self._mount_point+'/netcam/'
        if self.is_debug_mode():
            return self.DEVELOPMENT_PATH
        else:
            return self.PRODUCTION_PATH

    def get_log_filename(self):
        """ get the current fully qualified log filename """
        fname = self.get_standard_path() + self.LOG_FILE_NAME
        ymd = datetime.now().strftime('%Y.%m.%d')
        fname = fname.replace("?", ymd)
        return fname # logfile for Flask + recorder applications

    def get_video_filename(self, idx):
        """ get the fully qualified video filename """
        fname = self.get_standard_path() + self.VIDEO_FILE_NAME
        fname = fname.replace("?1", str(idx))
        dt = datetime.now().strftime('%Y.%m.%d.%H.%M.%S')
        fname = fname.replace("?2", dt)
        return fname, dt # video file name and timestamp for recorder 'idx'

    def get_flask_secret(self):
        """ get the Flask secret for the session variable """
        return self._flask_secret

    def get_error_messages(self):
        """ get error messages from the initialization part """
        return self.msgs

if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
