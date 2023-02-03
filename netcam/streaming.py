# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland

import threading

class Streaming:
    """ class for facilitating video streaming, once per user """
    def __init__(self):
        """ initialize streaming list:
                empty: no video streaming allowed for any users
                not empty: video streaming allowed for each userid in list
        """
        self._streams = []
        self._mutex = threading.Semaphore(1)

    def _set_stream(self, userid):
        """ add userid to list """
        if userid not in self._streams:
            self._streams.append(userid)
            return True # success
        return False # failed

    def _get_stream(self, userid):
        """ True if userid in list, else not """
        return userid in self._streams

    def _del_stream(self, userid):
        """ remove userid from list """
        if userid in self._streams:
            self._streams.remove(userid)
            return True # success
        return False # failed

    def set_context(self, userid, streaming=False):
        """ set the streaming context for each user """
        with self._mutex:
            if streaming:
                success = self._set_stream(userid)
            else:
                success = self._del_stream(userid)
            return success

    def is_allowed(self, userid):
        """ check if streaming is allowed for the user """
        with self._mutex:
            return self._get_stream(userid)
