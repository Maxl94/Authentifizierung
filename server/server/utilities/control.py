from threading import Thread
from .alarm import Alarm
from .hw import bno
import time


class Control(Thread):

    def __init__(self, config):
        print("started init")
        super().__init__()
        self.sensor_timeout = 3
        self.config = config
        self.alarm = Alarm()
        self.gyro = bno.Gyro()

        self.start_sensors()
        self.start()
        print("finished init")

    def run(self):
        print("Control Thread started")
        self.check_sensors()

    # ----- general methods -----
    # method looks for active sensors and if the want to request an alarm
    def check_sensors(self):
        while True:
            print("checking active sensors")
            print("gyro is active: ", self.config.gyro_sensor_is_active)
            if self.config.sound_alarm_is_active:
                if self.config.gyro_sensor_is_active:
                    self.check_sensor_gyro()
                if self.config.ir_sensor_is_active:
                    self.check_sensor_ir()
                if self.config.light_sensor_is_active:
                    self.check_sensor_light()
            time.sleep(self.sensor_timeout)

    # method to update config, config includes all active sensors and utility
    def update_config(self, config):
        print("updating config")
        self.config = config
        print("update completed")

    def start_sensors(self):
        print("starting sensors")
        self.gyro.start()
        # ir
        # light

    # ----- alarm methods -----
    # methods to start and stop an alarm sound
    def start_alarm(self):
        print("requesting alarm")
        self.alarm.start_alarm(self.config.alarm_duration)

    def stop_alarm(self):
        print("requesting to stop alarm")
        self.alarm.stop_alarm()

    # ----- sensor methods -----
    def check_sensor_gyro(self):
        print("checking sensor: gyro")
        if self.gyro.was_moved():
            print("backpack moved, starting alarm")
            self.start_alarm()
        else:
            print("backpack was not moved")

    def check_sensor_ir(self):
        print("checking sensor: ir")
        # TODO get boolean from ir if alarm is required

    def check_sensor_light(self):
        print("checking sensor: light")
        # TODO get boolean from light if alarm is required
