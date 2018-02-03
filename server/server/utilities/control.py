from threading import Thread
import time
from .alarm import Alarm
from .hw import bno
from .hw import ldr_modul
from .hw import ir_modul
from .hw import motion_det
from .hw import gps_modul
from geopy.distance import vincenty

class Control(Thread):
    # TODO: rename dummy_safe_zone to a more fitting name (i.e. something with list)
    def __init__(self, config, dummy_safe_zone, db_is_ready=True):
        print("started init")
        super().__init__()
        if db_is_ready:
            self.sensor_timeout = 0.01  # in seconds
            self.ir_threshold = 20

            self.gps_array = [0, 0]
            self.old_gps_array = [0, 0]
            self.gps_diff_threshold = 50  # in meters

            self.config = config
            self.dummy_safe_zone = dummy_safe_zone

            # init sensors
            self.alarm = Alarm()
            self.gyro = bno.Gyro()
            self.ir = ir_modul.IrI2c()
            self.motion = motion_det.MotionDetection()
            self.gps = gps_modul.gps_uart()

            # TODO fix light sensor
            # self.light = ldr_modul.Ldr()

            self.start_sensors()
            self.start()
        print("finished init")

    def run(self):
        print("Control Thread started")
        self.check_sensors()

    # ----- general methods -----
    # method looks for active sensors and if they want to request an alarm
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
            
            self.update_gps_data()
            if self.check_gps_diff():
                # TODO handle return from check_safe_zones()
                self.check_safe_zones()

            time.sleep(self.sensor_timeout)

    # method to update config, config includes all active sensors and utilities
    def update_config(self, config):
        print("updating config")
        self.config = config
        print("update completed")

    def start_sensors(self):
        print("starting sensors")
        self.gps.start()
        self.gyro.start()
        ir_modul.initIRPack()
        self.motion.start()

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
        self.old_gps_array = self.gps_array[:]
        self.gps_array = [self.gps.get_data().lat, self.gps.get_data().long]

        # TODO fix in gps module
        _lat = self.gps.get_data().lat
        _long = self.gps.get_data().lat
        #print('DEBUG: GPS {0}:{1}'.format(self.gps.get_data().lat, self.gps.get_data().long))
        if _lat.replace(' ', '') != '' and _long.replace(' ', ''):
            _flat = str(self.gps.get_data().lat).split(',')
            _flong = str(self.gps.get_data().long).split(',')
            self.dummy_safe_zone.latitude = float(_flat[0])
            self.dummy_safe_zone.longitude = float(_flong[0])

            # FIXME untested: should override db object from django
            self.dummy_safe_zone.save()
            print('GPS data saved')
        else:
            print('No GPS data available')

    def check_gps_diff(self):
        gps_diff = vincenty(self.old_gps_array, self.gps_array).meters
        if gps_diff >= self.gps_diff_threshold:
            return True
        else:
            return False

    def check_safe_zones(self):
        print("checking if inside of a safe zone")
        for item in self.safe_zone_list:
            safe_zone_cords = [item.latitude, item.longitude]
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