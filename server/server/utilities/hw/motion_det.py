import numpy as np
import cv2
import socket
import json
import threading
import ast
from time import sleep

from pyparsing import col

UDP_IP = "127.0.0.1"
UDP_PORT = 55555


class MotionDetection(threading.Thread):

    def remove_prefix(self, text, prefix):
        return text[text.startswith(prefix) and len(prefix):]

    def run(self):
        while self.run_event.is_set():
            #k = cv2.waitKey(50) & 0xff
            self.sock.sendto(b'THERMAL_REQ', (UDP_IP, UDP_PORT))
            udp = self.sock.recvfrom(2048)
            udp_data = udp[0]
            if udp_data.startswith(b'THERMAL_DATA'):
                udp_data = self.remove_prefix(udp_data, b'THERMAL_DATA\n')
                json_data = json.loads(udp_data.decode('utf-8'))
                if 'data' in json_data and 'ambient' in json_data:
                    data = np.asarray(json_data["data"])
                    data = data.astype(np.float)
                    cscale = 255 / (data.max())
                    shift = -1 * (data.min())
                    size = data.shape
                    thermal_img = np.zeros(size, dtype='uint8')
                    self.fgmask = np.zeros(size, dtype='uint8')
                    thermal_img = cv2.convertScaleAbs(data, thermal_img, cscale, shift / 255.0)
                    colorFrame = cv2.cvtColor(thermal_img, cv2.COLOR_GRAY2BGR)
                    colorFrame = cv2.resize(colorFrame, (0,0), fx=40.0, fy=40.0, interpolation=cv2.INTER_NEAREST)
                    self.out.write(colorFrame)
                    #cv2.imshow("Input, scaled", colorFrame)

                    learning_rate = -1
                    if np.max(data) > (json_data["ambient"] + 1):
                        learning_rate = 0
                    self.fgmask = self.fgbg.apply(data, self.fgmask, learning_rate)
                    #cv2.imshow('Background removed', self.fgmask)
            #if k == 27:
            #    break

    def close(self):
        self.out.release()
        cv2.destroyAllWindows()
        self.run_event.clear()

    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=4, detectShadows=False)
        self.fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        self.out = cv2.VideoWriter('out.avi', self.fourcc, 20.0, (640, 160))
        self.run_event = threading.Event()
        self.run_event.set()
        self.fgmask = 0

    def get_filtered_data_percent(self):
        return np.mean(self.fgmask)

if __name__ == "__main__":
    motion_det = MotionDetection()
    motion_det.start()
    try:
        while motion_det.is_alive():
            sleep(0.1)
            print(motion_det.get_filtered_data_percent())

    except KeyboardInterrupt:
        motion_det.close()
        motion_det.join()
