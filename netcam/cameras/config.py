# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# config class modul for retrieving non-public information, e.g. may contain some credentials you do not want to share.
import logging
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
    DEVELOPMENT_LOGFILE_NAME = 'netcam.log'
    PRODUCTION_LOGFILE_NAME = '/var/log/netcam.log'

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
        # set debug_mode info
        mynode = platform.uname().node
        self._debug_mode = (mynode == 'macbook.local' or mynode == 'nvr')
        pass

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

    def get_ip_address_list(self):
        """ get the list of IP addresses of the network cameras """
        ips = []
        for idx in range(len(self._config)):
            ips.append(self._config[idx]['ip'])
        return ips

    def get_rtsp_url(self, idx):
        """ get the rtsp url for indexed camera device, zero based index """
        ip = self.get_ip_address(idx)
        if isinstance(ip, int): # integer
            return ip # webcam index
        elif isinstance(ip, str):
            # ip address string, like '192.168.1.22'
            url = "rtsp://<user>:<password>@<ip>:554/H264/ch1/main/av_stream"
            url = url.replace('<user>', self.get_username(idx))
            url = url.replace('<password>', self.get_password(idx))
            url = url.replace('<ip>', ip) # ip address string
            return url
        else:
            raise TypeError('IP address should be an integer or string.')

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
