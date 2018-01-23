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

    def debug(self):
        print('Debugging:')
        print('is_locked: {0}'.format(self.is_locked))
        print('gps_is_active: {0}'.format(self.gps_is_active))
        print('light_sensor_is_active: {0}'.format(self.light_sensor_is_active))
        print('ir_sensor_is_active: {0}'.format(self.ir_sensor_is_active))
        print('gyro_sensor_is_active: {0}'.format(self.gyro_sensor_is_active))
        print('sound_alarm_is_active: {0}'.format(self.sound_alarm_is_active))
        print('alarm_duration: {0}'.format(self.alarm_duration))


class Savezone(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    radius = models.IntegerField(blank=False, null=False)
    x_cord = models.IntegerField(blank=False, null=False)
    y_cord = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return self.name