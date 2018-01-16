import time
import threading
from Adafruit_BNO055 import BNO055


class Gyro(threading.Thread):
    moved = False
    mutex = threading.Lock()

    def run(self):
        # Create an ew BNO055 instance
        bno = BNO055.BNO055(serial_port='/dev/ttyUSB0')

        # Initialize the BNO055 and stop if something went wrong.
        if not bno.begin():
            raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

        # Print system status and self test result.
        status, self_test, error = bno.get_system_status()
        print('System status: {0}'.format(status))
        print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))

        # Print out an error if system status is in error mode.
        if status == 0x01:
            print('System error: {0}'.format(error))
            print('See datasheet section 4.3.59 for the meaning.')

        # read the acceleration data
        print('Reading BNO055 data...')
        while True:
            # Read the linear acceleration (without gravity)
            x, y, z = bno.read_linear_acceleration()
            if abs(x) > 0.3 or abs(y) > 0.3 or abs(z) > 0.3:
                print('x={0:07.2F} y={1:07.2F} z={2:07.2F}'.format(x, y, z))
                self.mutex.acquire(blocking=True, timeout=-1)
                self.moved = True
                self.mutex.release()

            # Sleep for a second until the next reading.
            time.sleep(0.1)

    def was_moved(self):
        self.mutex.acquire(blocking=True, timeout=-1)
        moved = self.moved
        self.moved = False
        self.mutex.release()

        return moved

if __name__ == "__main__":
	g = Gyro()
	g.start()

	time.sleep(5)
	print("has moved: {}".format(g.was_moved()))
	time.sleep(5)
	print("has moved: {}".format(g.was_moved()))

