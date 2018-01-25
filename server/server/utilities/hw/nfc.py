# sudo apt-get install python-pyscard
from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import *
from smartcard.scard import *
from smartcard.pcsc.PCSCPart10 import (getFeatureRequest, hasFeature,FEATURE_CCID_ESC_COMMAND,SCARD_SHARE_SHARED)
from time import sleep
import threading

READER = 0

class NfcReaderObserver(CardObserver):
    def update(self, observable, actions):
        (addedcards, removedcards) = actions
        for card in addedcards:
            if card:
                hresult, hcard, dwActiveProtocol = SCardConnect(
                    self.hcontext,
                    self.reader,
                    SCARD_SHARE_SHARED,
                    SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
                if hresult != SCARD_S_SUCCESS:
                    print('Failed to connect to card : ' + SCardGetErrorMessage(hresult))
                    continue
                hresult, response = SCardTransmit(hcard, dwActiveProtocol, [0xFF, 0xCA, 0x00, 0x00, 0x04])
                if hresult != SCARD_S_SUCCESS:
                    print('Failed to read id : ' + SCardGetErrorMessage(hresult))
                    continue
                self.callback(1, toHexString(response, format=PACK | UPPERCASE))
                hresult, response = SCardTransmit(hcard, dwActiveProtocol, [0xFF, 0x00, 0x40, 0xAE, 0x04, 0x01, 0x04, 0x01, 0x00])
                if hresult != SCARD_S_SUCCESS:
                    print('Failed to sound and blink : ' + SCardGetErrorMessage(hresult))
                    continue
                SCardDisconnect(hcard, SCARD_LEAVE_CARD);

        for card in removedcards:
            self.callback(0, "")
            # hresult, hcard, dwActiveProtocol = SCardConnect(
            #         self.hcontext,
            #         self.reader,
            #         SCARD_SHARE_DIRECT,
            #         SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
            # if hresult != SCARD_S_SUCCESS:
            #     print('Failed to connect to card : ' + SCardGetErrorMessage(hresult))
            #     continue
            # hresult, response = SCardControl(hcard, SCARD_CTL_CODE(3500), [0xFF, 0x00, 0x40, 0xBE, 0x04, 0x01, 0x01, 0x10, 0x01])
            # if hresult != SCARD_S_SUCCESS:
            #     print('Failed to sound and blink : ' + SCardGetErrorMessage(hresult))
            #     continue
            # SCardDisconnect(hcard, SCARD_LEAVE_CARD)


    def __init__(self, callback):
        self.callback = callback
        self.reader = None
        try:
            hresult, self.hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
            if hresult != SCARD_S_SUCCESS:
                raise error('Failed to establish context : ' + SCardGetErrorMessage(hresult))
            hresult, readers = SCardListReaders(self.hcontext, [])
            if len(readers) < READER:
                raise error('No smart card readers')
            self.reader = readers[READER]
        except error as e:
            raise ConnectionError("Smart Card Error: {}".format(e))

class NfcReader(threading.Thread):
    def _disable_buz(self):
        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        assert hresult == SCARD_S_SUCCESS
        hresult, readers = SCardListReaders(hcontext, [])
        assert len(readers) > 0
        reader = readers[READER]
        hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, reader, SCARD_SHARE_DIRECT, SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
        print('Connected with active protocol', dwActiveProtocol)
        hresult, response = SCardControl(hcard, SCARD_CTL_CODE(1), [0xFF, 0x00, 0x52, 0x00, 0x00])
        if hresult != SCARD_S_SUCCESS:
            print('Failed to disable sound output : ' + SCardGetErrorMessage(hresult))


    def __init__(self, callback):
        threading.Thread.__init__(self)
        #self._disable_buz()

        self.cardmonitor = CardMonitor()
        self.cardobserver = NfcReaderObserver(callback)
        self.cardmonitor.addObserver(self.cardobserver)
        self.run_event = threading.Event()
        self.run_event.set()

    def run(self):
        while self.run_event.is_set():
            sleep(1)
    def close(self):
        self.run_event.clear()
        self.cardmonitor.deleteObserver(self.cardobserver)


def callback_func(status, id):
    #Callback, mit id als z.B AAB1020C9040 d.h. 5 Bytes UID
    if status == 1:
        print("Card with ID {} inserted".format(id))
    else:
        print("Card removed")


if __name__ == "__main__":
    read = NfcReader(callback_func)
    read.start()
    try:
        while read.is_alive():
            sleep(1)

    except KeyboardInterrupt:
        read.close()
        read.join()


