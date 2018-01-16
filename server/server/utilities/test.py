
from control import Control
import time


class Config:
    alarm_duration = 15
    sound_alarm_is_active = True

    gyro_is_active = False
    ir_is_active = False
    light_is_active = False
    temp_is_active = True
    test_is_active = False


class Config2:
    alarm_duration = 15

    gyro_is_active = False
    ir_is_active = False
    light_is_active = False
    sound_alarm_is_active = False
    temp_is_active = False
    test_is_active = False


print("loading config2 no sensor")
control = Control(Config2())
time.sleep(10)
print("loading config temp sensors active")
control.update_config(Config())
time.sleep(4)
control.stop_alarm()
