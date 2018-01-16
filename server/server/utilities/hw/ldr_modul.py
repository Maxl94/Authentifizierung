import logging
try:
    import RPi.GPIO as GPIO
    import time
except ImportError:
    logging.exception("failed to import 'RPi.GPIO'.")
LED_CH = 7
LDR_CH = 4
BOUNCE_MS = 1
class Ldr():
    def _ldr_callback_toogle(self, channel):
        self.state = 0x01

    def _addEvent(self, direction):
        GPIO.add_event_detect(LDR_CH, direction, callback=self._ldr_callback_toogle, bouncetime=BOUNCE_MS)

    def __init__(self):
        self.state = -1
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LDR_CH, GPIO.IN)
        GPIO.setup(LED_CH, GPIO.OUT)
        self.state = GPIO.input(LDR_CH)
        self._addEvent(GPIO.RISING)
    def close(self):
        GPIO.remove_event_detect(LDR_CH)
        GPIO.cleanup()

    def get_pin(self):
        tmp = self.state
        self.state = 0;
        return tmp


if __name__ == "__main__":
    ldr_inst = Ldr()
    while True:
        print(ldr_inst.get_pin())
        time.sleep(1)
