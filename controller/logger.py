import json
import time

class Logger:
    def __init__(self, logFile, mode='a'):
        self.logFile = logFile
        self.fd = open(self.logFile, mode)

    def error(self, endpoint, request, session, error):
        error = json.dumps(
            {
                'type'      :   "ERROR",
                'timestamp' :   time.time(),
                'endpoint'  :   str(endpoint),
                'request'   :   str(request),
                'session'   :   str(session),
                'error'     :   str(error)
            }
        )
        print(error)
        self.fd.write(error + '\n')
        self.fd.flush()
