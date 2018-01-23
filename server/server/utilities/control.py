from threading import Thread
from .alarm import Alarm
from .hw import bno
from .hw import ldr_modul
from .hw import ir_modul
from .hw import motion_det
from geopy.distance import vincenty
import time


class Control(Thread):

    def __init__(self, config, dummy_safe_zone):
        print("started init")
        super().__init__()
        self.sensor_timeout = 0.01  # in seconds
        self.ir_threshold = 20

        self.gps_array = [0, 0]
        self.old_gps_array = [0, 0]
        self.gps_diff_threshold = 50  # in meters

        self.config = config
        self.dummy_safe_zone = dummy_safe_zone

        self.alarm = Alarm()
        self.gyro = bno.Gyro()
        self.ir = ir_modul.IrI2c()
        self.motion = motion_det.MotionDetection()
        # TODO fix light sensor
        # self.light = ldr_modul.Ldr()

        self.start_sensors()
        self.start()
        print("finished init"   )

    def run(self):
        print("Control Thread started")
        self.check_sensors()

    # ----- general methods -----
    # method looks for active sensors and if the want to request an alarm
    def check_sensors(self):
        while True:
            # print("checking active sensors")
            # self.config.debug()
            # ----- alarm sensors ---------
            if self.config.sound_alarm_is_active:
                if self.config.gyro_sensor_is_active:
                    self.check_sensor_gyro()
                if self.config.ir_sensor_is_active:
                    self.check_sensor_ir()
                # if self.config.light_sensor_is_active:
                    # TODO fix light sensor
                    # self.check_sensor_light()

            # ----- gps sensor ----------
            if self.config.gps_is_active:
                self.update_gps_data()
                if self.check_gps_diff():
                    # TODO handle return from check_safe_zones()
                    self.check_safe_zones()

            time.sleep(self.sensor_timeout)

    # method to update config, config includes all active sensors and utility
    def update_config(self, config):
        print("updating config")
        self.config = config
        print("update completed")

    def start_sensors(self):
        print("starting sensors")
        self.gyro.start()
        ir_modul.initIRPack()
        self.motion.start()

    # ----- alarm methods -----
    # methods to start and stop an alarm sound
    def start_alarm(self):
        print("requesting alarm")
        self.alarm.start_alarm(self.config.alarm_duration)

    def stop_alarm(self):
        print("requesting to stop alarm")
        self.alarm.stop_alarm()

    # ----- gps methods -----
    # write gps data to django database on regular bases
    def update_gps_data(self):
        print("updating gps data")
        self.old_gps_array = self.gps_array

        # TODO Impl real gps check here
        self.gps_array = [48.85, 2.29]

        self.dummy_safe_zone.x_cord = self.gps_array[0]
        self.dummy_safe_zone.y_cord = self.gps_array[1]

        self.save()

    def check_gps_diff(self):
        gps_diff = vincenty(self.old_gps_array, self.gps_array).meters
        if gps_diff >= self.gps_diff_threshold:
            return True
        else:
            return False

    def check_safe_zones(self):
        print("checking if inside of a safe zone")
        for item in self.safe_zone_list:
            safe_zone_cords = [item.x_cord, item.y_cord]
            diff_from_safe = vincenty(safe_zone_cords, self.gps_array).meters
            if diff_from_safe <= item.radius:
                print("inside of a safe zone")
                return True
        print("not inside of a safe zone")
        return False

    # ----- sensor methods -----
    def check_sensor_gyro(self):
        print("checking sensor: gyro")
        if self.gyro.was_moved():
            print("backpack moved: starting alarm")
            self.start_alarm()
        else:
            print("backpack was not moved")

    def check_sensor_ir(self):
        print("checking sensor: ir")
        print("Motion filtered data percent value: {}".format(self.motion.get_filtered_data_percent()))
        if self.motion.get_filtered_data_percent() > self.ir_threshold:
            print("temperature change detected: alarm started")
            self.start_alarm()
        else:
            print("no significant temperature change detected")

    def check_sensor_light(self):
        print("checking sensor: light")
        if self.light.get_pin():
            print("light change detected: starting alarm")
            self.start_alarm()
        else:
            print("no light changes detected")