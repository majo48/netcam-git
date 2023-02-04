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

    def _set_stream(self, usrthrd):
        """ add userid to list """
        if usrthrd not in self._streams:
            self._streams.append(usrthrd)
            return True # success
        return False # failed

    def _del_stream(self, usrthrd):
        """ remove all items with userid from list """
        userid = usrthrd[0]
        success = False
        for item in self._streams:
            if item[0] == userid:
                self._streams.remove(item)
                success = True
        return success

    def set_context(self, userid, thread, streaming=False):
        """ set the streaming context for each user """
        with self._mutex:
            usrthrd = ( userid, thread )
            if streaming:
                success = self._set_stream(usrthrd)
            else:
                success = self._del_stream(usrthrd)
            return success

    def is_allowed(self, userid, thread):
        """ check if streaming is allowed for the user and thread """
        with self._mutex:
            usrthrd = ( userid, thread )
            for item in self._streams:
                if item == usrthrd:
                    return True # success
            return False # failed
