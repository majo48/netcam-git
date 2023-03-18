# Copyright (c) 2022 Martin Jonasse, Zug, Switzerland
#
# Composite class for receiving socket requests with logging objects
# based upon standard process defined in https://docs.python.org/3/howto/logging-cookbook.html

import pickle
import logging
import logging.handlers
import socketserver
import struct
import threading


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """
    Handler for a streaming logging request.
    This basically logs the record using whatever logging policy is
    configured locally at the receiver.
    """
    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            try:
                chunk = self.connection.recv(4)
            except ConnectionResetError:
                # connection reset by peer
                break # try again (silent)
            if len(chunk) < 4:
                break # try again (silent)
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """
    allow_reuse_address = True

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


class Tcpserver(threading.Thread):
    """
    handle the logging requests from all netcam-recorder.py processes
    this uses the same logging format as defined in netcam-app.py
    """
    def __init__(self):
        """ initialise the thread"""
        threading.Thread.__init__(self) # init super class
        self._tcpserver = LogRecordSocketReceiver()
        pass # continue

    def run(self):
        """run thread, called automatically """
        self._tcpserver.serve_until_stopped()
        pass # continue here after abort = 1

    def terminate_thread(self):
        """ stop running this thread, called when main thread terminates """
        self._tcpserver.abort = 1
        pass # continue
