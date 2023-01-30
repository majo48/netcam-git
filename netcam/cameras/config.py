# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# config class modul for retrieving non-public information, e.g. may contain some credentials you do not want to share.

import os
from dotenv import load_dotenv
import platform


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
        self._user = os.getenv('ANNKE_USER')
        self._password = os.getenv('ANNKE_PASSWORD')
        ipx = os.getenv('ANNKE_IPS')
        ipx = ipx.replace(" ", "")
        self._ips = list(ipx.split(";"))
        # set debug_mode info
        mynode = platform.uname().node
        self._debug_mode = (mynode == 'macbook.local' or mynode == 'nvr')
        pass

    def get_username(self):
        """ get the common username for accessing the network cameras """
        return self._user

    def get_password(self):
        """ get the common password for accessing the network cameras """
        return self._password

    def get_ip_adresse_list(self):
        """ get the list of IP addresses of the network cameras """
        return self._ips

    def get_rtsp_url(self, index):
        """ get the rtsp url for indexed ANNKE device, zero based index """
        url = "rtsp://<user>:<password>@<ip>:554/H264/ch1/main/av_stream"
        url = url.replace('<user>', self._user)
        url = url.replace('<password>', self._password)
        if (index >= 0) and (index < len(self._ips)):
            ip = self._ips[index]
            if ip.isnumeric(): # integer
                return int(ip) # webcam index
            else:              # string
                url = url.replace('<ip>', ip) # ip address string
                return url
        else:
            raise Exception('Network camera device index is out of range.')

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
