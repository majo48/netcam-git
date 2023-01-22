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
    def __init__(self):
        """ initialize an instance of the class """
        load_dotenv()
        # set confidential info
        self.user = os.getenv('ANNKE_USER')
        self.password = os.getenv('ANNKE_PASSWORD')
        ipx = os.getenv('ANNKE_IPS')
        ipx = ipx.replace(" ", "")
        self.ips = list(ipx.split(";"))
        # set debug_mode info
        mynode = platform.uname().node
        self.debug_mode = (mynode == 'macbook.local' or mynode == 'nvr')
        pass

    def get_username(self):
        """ get the common username for accessing the network cameras """
        return self.user

    def get_password(self):
        """ get the common password for accessing the network cameras """
        return self.password

    def get_ip_adresse_list(self):
        """ get the list of IP addresses of the network cameras """
        return self.ips

    def get_rtsp_url(self, index):
        """ get the rtsp url for indexed ANNKE device, zero based index """
        url = "rtsp://<user>:<password>@<ip>:554/H264/ch1/main/av_stream"
        url = url.replace('<user>', self.user)
        url = url.replace('<password>', self.password)
        if (index >= 0) and (index < len(self.ips)):
            url = url.replace('<ip>', self.ips[index])
            return url
        else:
            raise Exception('Network camera device index is out of range.')

    def is_debug_mode(self):
        """ get DEBUG_MODE variable """
        return self.debug_mode

    def is_production_mode(self):
        """ get inverted DEBUG_MODE variable """
        return not self.is_debug_mode()

