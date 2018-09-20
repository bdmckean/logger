import pickle
import logging
import logging.handlers
import socketserver
import struct
#
# from https://docs.python.org/3/howto/logging-cookbook.html#network-logging
#

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
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

def run_logger():
    logging.basicConfig(
        format='%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s')
    tcpserver = LogRecordSocketReceiver()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    pipe_logger = logging.getLogger('project')
    pipe_logger.setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    request_log = logging.getLogger("requests")
    request_log.setLevel(logging.WARNING)
    urllib3_log = logging.getLogger("urllib3")
    urllib3_log.setLevel(logging.CRITICAL)
    h = logging.handlers.RotatingFileHandler('/var/log/project/log.log', 'a', maxBytes=20*1024*1024, backupCount=10)
    f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
    h.setFormatter(f)
    pipe_logger.addHandler(h)
    print('About to start TCP server...')
    tcpserver.serve_until_stopped()

if __name__ == '__main__':
    run_logger()
