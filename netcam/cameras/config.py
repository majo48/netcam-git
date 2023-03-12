# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# config class modul for retrieving non-public information, e.g. may contain some credentials you do not want to share.

import logging
import sys
import os
from dotenv import load_dotenv
import platform
import json


class Config:
    """
    This is place to define the hardware and software configuration parameters for accessing the network cameras.
    The cameras have common usernames and passwords for accessing the video information, however the IP addresses
    are unique; one IP for each camera (fixed IP addresses).
    - Confidential information is kept in the .env file (root or user folder)
    - Hardware information will define the DEBUG_MODE: True or False
    - Other information can be defined as constants in this config.py file
    """
    DEVELOPMENT_LOGFILE_NAME = 'netcam.log' # [default]
    PRODUCTION_LOGFILE_NAME = '/var/log/netcam.log' # [default]

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
        for idx in range(len(self._config)):
            if "ttl" not in self._config[idx]: logging.error("Missing 'ttl' in .ENV FLASK_CAM" + str(idx))
            if "usr" not in self._config[idx]: logging.error("Missing 'usr' in .ENV FLASK_CAM" + str(idx))
            if "pw" not in self._config[idx]: logging.error("Missing 'pw' in .ENV FLASK_CAM" + str(idx))
            if "ip" not in self._config[idx]: logging.error("Missing 'ip' in .ENV FLASK_CAM" + str(idx))
            if "fps" not in self._config[idx]: logging.error("Missing 'fps' in .ENV FLASK_CAM" + str(idx))
            if "roi" not in self._config[idx]: logging.error("Missing 'roi' in .ENV FLASK_CAM" + str(idx))
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
        same for netcam-app.py and netcam-recorder.py
        """
        myfmt = '%(asctime)s | %(levelname)s | %(process)d | %(threadName)s | %(module)s | %(message)s'
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
            lggr.setLevel(logging.DEBUG)
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
                level='INFO')
        pass

    def is_debug_mode(self):
        """ get DEBUG_MODE variable """
        return self._debug_mode

    def is_production_mode(self):
        """ get inverted DEBUG_MODE variable """
        return not self.is_debug_mode()

    def get_log_filename(self):
        """ get the current logfile (relative or absolute) """
        if self.is_debug_mode():
            return self.DEVELOPMENT_LOGFILE_NAME
        else:
            return self.PRODUCTION_LOGFILE_NAME

    def get_flask_secret(self):
        """ get the Flask secret for the session variable """
        return self._flask_secret


if __name__ == '__main__':
    print(
        'So sorry, the ' +
        os.path.basename(__file__) +
        ' module does not run as a standalone.')
