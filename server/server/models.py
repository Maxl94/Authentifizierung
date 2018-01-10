from django.db import models

class Setting(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    description = models.CharField(max_length=120, blank=False, null=False)
    is_locked = models.BooleanField(default=False)
    gps_is_active = models.BooleanField(default=False)
    light_sensor_is_active = models.BooleanField(default=False)
    ir_sensor_is_active = models.BooleanField(default=False)
    gyro_sensor_is_active = models.BooleanField(default=False)
    sound_alarm_is_active = models.BooleanField(default=False)
    alarm_duration = models.IntegerField(default=120)

    def __str__(self):
        return self.name