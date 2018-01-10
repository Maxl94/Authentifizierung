#!/usr/bin/env python

import sys
import pynmea2
import serial
import time
import threading
import copy
from collections import namedtuple

def TimerReset(*args, **kwargs):
    """ Global function for Timer """
    return _TimerReset(*args, **kwargs)


class _TimerReset(threading.Thread):
    """Call a function after a specified number of seconds:
    t = TimerReset(30.0, f, args=[], kwargs={})
    t.start() - to start the timer
    t.reset() - to reset the timer
    t.cancel() # stop the timer's action if it's still waiting
    """

    def __init__(self, interval, function, args=[], kwargs={}):
        threading.Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()
        self.resetted = True

    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()

    def run(self):
        #~ print("Time: %s - timer running..." % time.asctime())

        while self.resetted:
            #~ print("Time: %s - timer waiting for timeout in %.2f..." % (time.asctime(), self.interval))
            self.resetted = False
            self.finished.wait(self.interval)

        if not self.finished.isSet():
            self.function(*self.args, **self.kwargs)
        self.finished.set()
        #~ print("Time: %s - timer finished!" % time.asctime())

    def reset(self, interval=None):
        """ Reset the timer """

        if interval:
            #~ print("Time: %s - timer resetting to %.2f..." % (time.asctime(), interval))
            self.interval = interval
        #~ else:
            #~ print("Time: %s - timer resetting..." % time.asctime())

        self.resetted = True
        self.finished.set()
        self.finished.clear()

class gps_uart(threading.Thread):
    data_lock = threading.Lock()
    gps_store = None
    timer = None
    timer_interval = 10
    checksum_error_last_h = 0

    def clear_gps_store(self):
        self.data_lock.acquire(blocking=True, timeout=-1)
        self.gps_store.altitude = ""
        self.gps_store.lat = ""
        self.gps_store.long = ""
        self.gps_store.utc_time = None
        self.gps_store.nr_sat = 0
        self.data_lock.release()

    def timeout_msg(self):
        self.clear_gps_store()
        self.timer.reset()

    def run(self, port="/dev/ttyUSB0", baud=9600):
        global run_state
        run_state = True
        com = None
        reader = pynmea2.NMEAStreamReader(errors='ignore')

        while run_state:
            if com is None:
                try:
                    com = serial.Serial(port, baudrate=baud, timeout=5.0)
                except serial.SerialException:
                    print('could not connect to %s, trying again in 5 sec' % port)
                    time.sleep(5.0)
                    continue

            data = com.read(16)
            try:
                for msg in reader.next(data.decode('ascii', errors='ignore')):
                    if msg.sentence_type == 'GGA':
                        if msg.is_valid:
                            self.data_lock.acquire(blocking=True, timeout=-1)
                            self.gps_store.altitude = "%.2f" % msg.altitude + msg.altitude_units
                            self.gps_store.lat = "%.8f" % msg.latitude + "," + msg.lat_dir
                            self.gps_store.long = "%.8f" % msg.longitude + "," + msg.lon_dir
                            self.gps_store.utc_time = msg.__getattr__('timestamp')
                            self.gps_store.nr_sat = msg.__getattr__('num_sats')
                            self.data_lock.release()
                            self.timer.reset()
                        else:
                            self.clear_gps_store()
            except pynmea2.ChecksumError:
                checksum_error_last_h = checksum_error_last_h + 1
                continue
    def get_data(self):
        self.data_lock.acquire(blocking=True, timeout=100)
        t = copy.deepcopy(self.gps_store)
        self.data_lock.release()
        return t
    def __init__(self):
        threading.Thread.__init__(self)
        self.gps_store = namedtuple("GPSData", "utc_time long lat altitude nr_sat")
        self.clear_gps_store()
        self.timer = TimerReset(self.timer_interval, self.timeout_msg)
        self.timer.start()

if __name__ == "__main__":
    thread = gps_uart()
    thread.start()
    while True:
        print("Akt. Altitude: " + thread.get_data().altitude)
        time.sleep(10)