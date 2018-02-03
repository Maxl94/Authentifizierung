import pygame


class Alarm:

    # sound by soundbible.com http://soundbible.com/1937-Tornado-Siren-II.html
    sound_file_path = "/home/pi/Authentifzierung/server/server/utilities/Sirene.wav"

    def __init__(self):
        pygame.init()
        self.sound = pygame.mixer.Sound(self.sound_file_path)
        self.sound.set_volume(1.0)

    def start_alarm(self, duration):
        print("got alarm request")
        if not pygame.mixer.get_busy():
            print("start alarm")
            self.sound.play(maxtime=duration * 1000)
        else:
            print("alarm already playing")

    def stop_alarm(self):
        print("got stop alarm request")
        if pygame.mixer.get_busy():
            self.sound.stop()
            print("stopped alarm")
        else:
            print("no active alarm")
