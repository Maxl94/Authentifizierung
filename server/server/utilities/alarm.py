import pygame
import time


class Alarm:

    # sound by soundbible.com http://soundbible.com/1937-Tornado-Siren-II.html
    mixer = pygame.mixer
    is_playing = False
    sound_file_path = "Sirene.wav"

    def start_alarm(self, duration):
        print("got alarm request")
        pygame.init()
        self.mixer = pygame.mixer.Sound(self.sound_file_path)
        self.is_playing = True

        # play sound
        print("start alarm")
        self.mixer.play()
        time.sleep(duration)

        # stop alarm
        print("stopped alarm")
        self.mixer.stop()

    def stop_alarm(self):
        print("got stop alarm request")
        if self.is_playing:
            self.mixer.stop()
            print("stopped alarm")
        else:
            print("no active alarm")
