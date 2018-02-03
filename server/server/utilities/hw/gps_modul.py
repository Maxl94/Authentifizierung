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
    def __init__(self, interval, function, args=[], kwargs={}):
        threading.Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = threading.Event()
        self.resetted = True

    def cancel(self):
        self.finished.set()

    def run(self):
        while self.resetted:
            self.resetted = False
            self.finished.wait(self.interval)

        if not self.finished.isSet():
            self.function(*self.args, **self.kwargs)
        self.finished.set()

    def reset(self, interval=None):
        """ Reset the timer """

        if interval:
            self.interval = interval

        self.resetted = True
        self.finished.set()
        self.finished.clear()

class gps_uart(threading.Thread):
    data_lock = threading.Lock()
    gps_store = None
    timer = None
    timer_interval = 10

    def clear_gps_store(self):
        self.data_lock.acquire(blocking=True, timeout=-1)
        self.gps_store.altitude = None
        self.gps_store.lat = None
        self.gps_store.long = None
        self.gps_store.utc_time = None
        self.gps_store.nr_sat = 0
        self.data_lock.release()

    def timeout_msg(self):
        self.clear_gps_store()
        self.timer.reset()

    def run(self, port="/dev/ttyAMA0", baud=9600):
        com = None
        reader = pynmea2.NMEAStreamReader(errors='ignore')

        while self.run_event.is_set():
            if com is None:
                try:
                    com = serial.Serial(port, baudrate=baud, timeout=5.0)
                except serial.SerialException:
                    print('could not connect to %s, trying again in 5 sec' % port)
                    time.sleep(5.0)
                    continue
            try:
                data = com.read(16)
            except serial.SerialException:
                print('Can not read from %s, trying again in 1 sec' % port)
                time.sleep(1.0)
                continue
            try:
                for msg in reader.next(data.decode('ascii', errors='ignore')):
                    if msg.sentence_type == 'GGA':
                        if msg.is_valid:
                            self.data_lock.acquire(blocking=True, timeout=-1)
                            self.gps_store.altitude = "%.2f" % msg.altitude + msg.altitude_units
                            self.gps_store.lat = "%.8f" % msg.latitude
                            self.gps_store.long = "%.8f" % msg.longitude
                            self.gps_store.utc_time = msg.__getattr__('timestamp')
                            self.gps_store.nr_sat = msg.__getattr__('num_sats')
                            self.data_lock.release()
                            self.timer.reset()
                        else:
                            self.clear_gps_store()
            except pynmea2.ChecksumError:
                continue
    def get_data(self):
        self.data_lock.acquire(blocking=True, timeout=100)
        t = copy.deepcopy(self.gps_store)
        self.data_lock.release()
        return t
    def __init__(self):
        threading.Thread.__init__(self)
        self.run_event = threading.Event()
        self.run_event.set()
        self.gps_store = namedtuple("GPSData", "utc_time long lat altitude nr_sat")
        self.clear_gps_store()
        self.timer = TimerReset(self.timer_interval, self.timeout_msg)
        self.timer.start()
    def close(self):
        self.run_event.clear()

if __name__ == "__main__":
    gps_uart = gps_uart()
    gps_uart.start()
    try:
        while gps_uart.is_alive():
            print(gps_uart.get_data().lat)
            time.sleep(10)
    except KeyboardInterrupt:
        gps_uart.close()
        gps_uart.join()
