#!/usr/bin/env python
import logging
import threading
from enum import IntEnum
from math import sqrt
from time import sleep
import ctypes

from smbus2 import i2c_msg
import numpy as np

i2c_thread = None


class IrI2c(threading.Thread):
    data_lock = threading.Lock()

    def run(self):
        while self.run_event.is_set():
            self.ta = self._get_ptat()
            self._calc_ir()
            sleep(1.0 / self.refresh_rate_hz)

    def _read_32byte(self, addr, start):
        return self.smbus.read_i2c_block_data(addr, start, 32)

    def _read_data_no_step(self, chip_addr, cmd, read_addr, nr_bytes):
        write = None
        read = None
        try:
            write = i2c_msg.write(chip_addr, [cmd, read_addr, 0x00, nr_bytes - 1])
            read = i2c_msg.read(chip_addr, nr_bytes)
            self.smbus.i2c_rdwr(write, read)
        except IOError:
            logging.exception("Can not read from I2C Bus")
            self._init()
            return self._read_data_no_step(chip_addr, cmd, read_addr, nr_bytes)
        return bytearray(ctypes.string_at(read.buf, read.len))

    def _read_data_step(self, chip_addr, cmd, read_addr, addr_step, nr_bytes):
        write = None
        read = None
        try:
            write = i2c_msg.write(chip_addr, [cmd, read_addr, addr_step, nr_bytes])
            read = i2c_msg.read(chip_addr, (addr_step + 1) * nr_bytes)
            self.smbus.i2c_rdwr(write, read)
        except IOError:
            logging.exception("Can not read from I2C Bus")
            self._init()
            return self._read_data_step(chip_addr, cmd, read_addr, addr_step, nr_bytes)
        return bytearray(ctypes.string_at(read.buf, read.len))

    def _read_config(self):
        return self._read_data_no_step(self.smbus_addr_ir, self.chip_command.READ_VAL.value,
                                       self.ir_register.CONFIG.value, 0x02)

    def _read_ptat(self):
        return int.from_bytes(self._read_data_no_step(self.smbus_addr_ir, self.chip_command.READ_VAL.value,
                                                      self.ir_register.PTAT.value, 0x02), byteorder='little',
                              signed=True)

    def _read_compensation(self):
        return int.from_bytes(self._read_data_no_step(self.smbus_addr_ir, self.chip_command.READ_VAL.value,
                                                      self.ir_register.COMPENSATION.value, 0x02),
                              byteorder='little', signed=True)

    def _read_eeprom_content(self):
        for i in range(0, 8):
            eeprom_data = self._read_32byte(self.smbus_addr_eeprom, i * 32)
            if len(eeprom_data) != 32:
                logging.exception("Could not read EEPROM per I2C")
                return 0
            self.eeprom_dump[i * 32:i * 32 + 32] = eeprom_data
        if self.eeprom_dump[
           self.eeprom_register.CHIP_ID.value:self.eeprom_register.CHIP_ID.value + 0x08] != self.chip_id:
            logging.exception("Could not verify chip id, error in I2C comm")
            return 0
        return 1

    def _read_ir_raw(self):
        ir_data = self._read_data_step(self.smbus_addr_ir, self.chip_command.READ_VAL.value,
                                       self.ir_register.IrData.value, 0x01, 0x40)
        if ir_data == -1:
            return -1
        self.ir_data_raw = np.frombuffer(ir_data, dtype=np.int16, count=64)
        self.ir_data_raw = np.reshape(self.ir_data_raw, (4, 16), order='F')
        return 0

    def _test_por(self):
        val = self._read_config()
        return val[1] & 0x04

    def _precalc_ir(self):
        config_reg = (int)((self.config[0] >> 4) & 0x03)
        for y in range(0, self.y_size):
            for x in range(0, self.x_size):
                index = y + x * 4
                deltaai = self.eeprom_dump[index]
                # Compensation of wrong eeprom entries?!
                if y == 0 and x == 1:
                    deltaai = 0x07
                if y == 1 and x == 1:
                    deltaai = 0x08
                if y == 2 and x == 1:
                    deltaai = 0x07
                bi = int.from_bytes([self.eeprom_dump[0x40 + index]], byteorder='little', signed=True)
                self.deltaalpha[y][x] = int.from_bytes([self.eeprom_dump[0x80 + index]], byteorder='little',
                                                       signed=False) / pow(2, self.deltaalphascale)
                self.ai[y][x] = (self.acommon + deltaai * pow(2, self.aiscale)) / pow(2, 3 - config_reg)
                self.bi[y][x] = bi / (pow(2, self.biscale) * pow(2, 3 - config_reg))

        self.ks4 = self.ks4ee / pow(2, self.ksscale + 8.0)
        self.alpha_1 = self.alpha0 / pow(2, self.alpha0scale)
        self.alpha_cp = (float)(self.alphacp) / (pow(2, self.alpha0scale) * pow(2, 3 - config_reg))
        self.KsTa = (float)(self.ksta_raw) / pow(2, 20.0)
        self.TGC = (self.tgc / 32.0)
        self.epsilon = (self.epsilon_raw / 32768.0)

    def _calc_ir(self):
        while True:
            por_flag = self._test_por()
            if not por_flag:
                logging.exception("POR Flag Reset")
                sleep(0.5)
                self._init()
            if por_flag:
                break

        if self._read_ir_raw() == -1:
            return 0

        config_reg = (int)((self.config[0] >> 4) & 0x03)
        tak4 = pow((self.ta + 273.15), 4.0)
        vir_cp_offset_compensated = (float)(self.vcp) - (self.acp + self.bcp * (self.ta - 25.0))
        # Versuch das ganze mit einem Array in numpy zu realisieren

        vir = self.ir_data_raw.astype(np.float32)
        deltaalpha = np.array(self.deltaalpha, np.float32)
        ai = np.array(self.ai, np.float32)
        bi = np.array(self.bi, np.float32)

        ta_m25 = self.ta - 25.0
        # alpha_2 = self.deltaalpha[y][x]
        # alpha = (self.alpha_1 + alpha_2) / pow(2, 3-config_reg)
        deltaalpha += self.alpha_1
        res_shift = pow(2, 3 - config_reg)
        if (res_shift != 1):
            deltaalpha = np.divide(deltaalpha, res_shift)

        # alpha_compensated = (1.0 + self.KsTa * (self.ta - 25.0)) * -->> (alpha - self.TGC * self.alpha_cp)
        deltaalpha -= self.TGC * self.alpha_cp
        calc_helper = (1.0 + self.KsTa * ta_m25)
        deltaalpha = np.multiply(deltaalpha, calc_helper)

        # vir_offset_compensated = (float)(vir) - (self.ai[y][x] + self.bi[y][x] * (self.ta - 25.0))
        bi = np.multiply(bi, ta_m25)
        bi = np.add(bi, ai)
        vir_offset_compensated = np.subtract(vir, bi)

        # vir_tgc_compensated = vir_offset_compensated -  self.TGC * vir_cp_offset_compensated
        # vir_compensated = vir_tgc_compensated / self.epsilon
        calc_helper = self.TGC * vir_cp_offset_compensated
        vir_tgc_compensated = np.subtract(vir_offset_compensated, calc_helper)
        vir_compensated = np.divide(vir_tgc_compensated, self.epsilon)

        # sx = self.ks4 * pow(pow(alpha_compensated, 3.0) * vir_compensated + pow(alpha_compensated, 4.0) * tak4, 1 / 4.0)
        # to = pow((vir_compensated / (alpha_compensated * (1.0 - self.ks4 * 273.15) + sx)) + tak4, 1 / 4.0) - 273.15
        sx_data_1 = np.add(np.multiply(np.power(deltaalpha, 3.0), vir_compensated), np.multiply(np.power(deltaalpha, 4.0), tak4))
        sx = self.ks4 * np.power(sx_data_1, 0.25)

        #to_1 = np.multiply(deltaalpha, (1.0 - self.ks4 * 273.15))
        to_1 = np.add(np.multiply(deltaalpha, (1.0 - self.ks4 * 273.15)), sx)
        to_2 = np.add(np.divide(vir_compensated, to_1), tak4)
        to = np.subtract(np.power(to_2, 0.25), 273.15)

        if self.invert_x:
            to = np.flipud(to)
        if self.invert_y:
            to = np.fliplr(to)

        self.ir_data = to.tolist()

    def _get_ptat(self):
        tries = 0
        while True:
            ptat = self._read_ptat()
            tries = tries + 1
            if ptat == -1:
                sleep(0.05)
            if ptat != -1:
                break
            if tries >= 10:
                logging.exception("Can not read ptat")
                return -273.15

        return (((self.kt1 * -1.0) + sqrt(self.kt1 * self.kt1 - (4 * self.kt2) * (self.vth - ptat))) / (
                2 * self.kt2)) + 25.0

    def get_data(self):
        return self.ir_data

    def _init(self):
        if self.smbus is not None:
            self.smbus.close()
            self.smbus = None

        try:
            from smbus2 import SMBus
            self.smbus = SMBus(1)
        except ImportError:
            self.smbus = None
            logging.exception("failed to import 'smbus'. do you have 'python3-smbus2' installed?")
        except IOError:
            self.smbus = None
            logging.exception("failed to connect to SMBus. is the user member of the 'i2c' group?")

        sleep(0.005)

        if not self._read_eeprom_content():
            return 0

        # Write trim register
        trim_values = [self.eeprom_dump[self.eeprom_register.OSC_TRIM.value] - 0xAA,
                       self.eeprom_dump[self.eeprom_register.OSC_TRIM.value], 0x00 - 0xAA, 0x00]
        self.smbus.write_i2c_block_data(self.smbus_addr_ir, self.chip_command.TRIM_VAL.value, trim_values)

        # Write config register
        config_value = [self.config[0] - 0x55, self.config[0], self.config[1] - 0x55, self.config[1]]
        self.smbus.write_i2c_block_data(self.smbus_addr_ir, self.chip_command.WRITE_CMD.value, config_value)

        # Verify config register
        ver_conf = self._read_config()
        if ver_conf != self.config:
            logging.exception("Could not verify config")
            return 0
        config_reg = (int)((self.config[0] >> 4) & 0x03)

        # hex_string = "".join("\\x%02x" % b for b in self.eeprom_dump)
        # print(hex_string)
        self.vcp = self._read_compensation()
        self.acp = int.from_bytes(bytearray([self.eeprom_dump[self.eeprom_register.CAL_ACP_L.value],
                                             self.eeprom_dump[self.eeprom_register.CAL_ACP_H.value]]),
                                  byteorder='little', signed=True)
        self.bcpee = int.from_bytes([self.eeprom_dump[self.eeprom_register.CAL_BCP.value]], byteorder='little',
                                    signed=True)
        self.tgc = int.from_bytes([self.eeprom_dump[self.eeprom_register.CAL_TGC.value]], byteorder='little',
                                  signed=True)
        self.aiscale = self.eeprom_dump[self.eeprom_register.CAL_AI_SCALE.value] >> 4
        self.biscale = self.eeprom_dump[self.eeprom_register.CAL_BI_SCALE.value] & 0x0F
        self.alpha0 = int.from_bytes(bytearray([self.eeprom_dump[self.eeprom_register.CAL_A0_L.value],
                                                self.eeprom_dump[self.eeprom_register.CAL_A0_H.value]]),
                                     byteorder='little', signed=False)

        self.alpha0scale = self.eeprom_dump[self.eeprom_register.CAL_A0_SCALE.value]
        self.deltaalphascale = self.eeprom_dump[self.eeprom_register.CAL_DELTA_A_SCALE.value]
        self.ksta_raw = int.from_bytes(bytearray([self.eeprom_dump[self.eeprom_register.CAL_KSTA_L.value],
                                                  self.eeprom_dump[self.eeprom_register.CAL_KSTA_H.value]]),
                                       byteorder='little', signed=True)
        self.alphacp = int.from_bytes(bytearray([self.eeprom_dump[self.eeprom_register.CAL_alphaCP_L.value],
                                                 self.eeprom_dump[self.eeprom_register.CAL_alphaCP_H.value]]),
                                      byteorder='little', signed=True)

        self.epsilon_raw = int.from_bytes(bytearray([self.eeprom_dump[self.eeprom_register.CAL_EMIS_L.value],
                                                     self.eeprom_dump[self.eeprom_register.CAL_EMIS_H.value]]),
                                          byteorder='little', signed=False)
        self.acommon = int.from_bytes(bytearray([self.eeprom_dump[self.eeprom_register.CAL_ACOMMON_L.value],
                                                 self.eeprom_dump[self.eeprom_register.CAL_ACOMMON_H.value]]),
                                      byteorder='little', signed=True)
        self.ks4ee = int.from_bytes([self.eeprom_dump[self.eeprom_register.KS4_EE.value]], byteorder='little',
                                    signed=True)
        self.ksscale = self.eeprom_dump[self.eeprom_register.KS_SCALE.value] & 0x0F
        self.bcp = self.bcpee / (pow(2, self.biscale) * pow(2, 3 - config_reg))

        # Berechnungen für ptat
        self.vth = (self.eeprom_dump[self.eeprom_register.VTH_H.value] << 8) | (
            self.eeprom_dump[self.eeprom_register.VTH_L.value])

        if self.vth > 32767:
            self.vth -= 65536
            self.vth = self.vth / pow(2, 3 - config_reg)

        kt1 = (self.eeprom_dump[self.eeprom_register.KT1_H.value] << 8) | (
            self.eeprom_dump[self.eeprom_register.KT1_L.value])
        if kt1 > 32767:
            kt1 -= 65536

        exp1 = (self.eeprom_dump[self.eeprom_register.KT_SCALE.value] >> 4)
        self.kt1 = kt1 / (pow(2, exp1) * pow(2, 3 - config_reg))

        kt2 = (self.eeprom_dump[self.eeprom_register.KT2_H.value] << 8) | (
            self.eeprom_dump[self.eeprom_register.KT2_L.value])
        if kt2 > 32767:
            kt2 -= 65536

        exp1 = self.eeprom_dump[self.eeprom_register.KT_SCALE.value] & 0x0F
        self.kt2 = kt2 / (pow(2, exp1 + 10) * pow(2, 3 - config_reg))

        self._precalc_ir()

        self.ta = self._get_ptat()
        if self.ta > 300 or self.ta < -20:
            logging.exception("Invalid temp value, I2C connection error?")
            return 0

    def __init__(self):
        threading.Thread.__init__(self)
        self.smbus = None
        self.smbus_addr_eeprom = 0x50
        self.smbus_addr_ir = 0x60
        self.eeprom_dump = bytearray(256)
        self.chip_id = bytearray.fromhex('E4300D35682201C2')
        self.config = bytearray.fromhex('3946')  # LSB FIRST!
        self.invert_x = True
        self.invert_y = True
        self.ir_register = IntEnum(value='IrEnum',
                                   names=[('IrData', 0x00), ('PTAT', 0x40), ('COMPENSATION', 0x41), ('CONFIG', 0x92),
                                          ('TRIM', 0x93)])
        self.eeprom_register = IntEnum(value='RegisterEnum',
                                       names=[('KS_SCALE', 0xC0), ('KS4_EE', 0xC4), ('CAL_ACOMMON_L', 0xD0),
                                              ('CAL_ACOMMON_H', 0xD1), ('KT_SCALE', 0xD2), ('CAL_ACP_L', 0xD3),
                                              ('CAL_ACP_H', 0xD4), ('CAL_BCP', 0xD5), ('CAL_alphaCP_L', 0xD6),
                                              ('CAL_alphaCP_H', 0xD7), ('CAL_TGC', 0xD8), ('CAL_AI_SCALE', 0xD9),
                                              ('CAL_BI_SCALE', 0xD9), ('VTH_L', 0xDA), ('VTH_H', 0xDB), ('KT1_L', 0xDC),
                                              ('KT1_H', 0xDD), ('KT2_L', 0xDE), ('KT2_H', 0xDF), ('CAL_A0_L', 0xE0),
                                              ('CAL_A0_H', 0xE1), ('CAL_A0_SCALE', 0xE2), ('CAL_DELTA_A_SCALE', 0xE3),
                                              ('CAL_EMIS_L', 0xE4), ('CAL_EMIS_H', 0xE5), ('CAL_KSTA_L', 0xE6),
                                              ('CAL_KSTA_H', 0xE7), ('OSC_TRIM', 0xF7), ('CHIP_ID', 0xF8)])
        self.chip_command = IntEnum(value='CommandEnum',
                                    names=[('READ_VAL', 0x02), ('WRITE_CMD', 0x03), ('TRIM_VAL', 0x04)])
        self.x_size = 16
        self.y_size = 4
        #self.ir_data_raw = [[0 for x in range(self.x_size)] for y in range(self.y_size)]
        self.ir_data = [[0 for x in range(self.x_size)] for y in range(self.y_size)]
        self.ai = [[0 for x in range(self.x_size)] for y in range(self.y_size)]
        self.bi = [[0 for x in range(self.x_size)] for y in range(self.y_size)]
        self.deltaalpha = [[0 for x in range(self.x_size)] for y in range(self.y_size)]
        self.refresh_rate_hz = 512 if (self.config[0] & 0x0F) < 6 else pow(2, (0xF - (self.config[0] & 0x0F))) * 0.5
        self.run_event = threading.Event()
        self.run_event.set()

        return self._init()
    def close(self):
        self.run_event.clear()

    def get_ambient_temp(self):
        return self.ta


from socketserver import UDPServer, BaseRequestHandler
import socket
import json

PORT = 55555


class UDPServerThread(threading.Thread):
    server = None
    def run(self):
        addr = ("", PORT)
        print("UDP server listening on", addr)
        self.server = UDPServer(addr, Handler)
        self.server.serve_forever()
    def shutdown(self):
        self.server.shutdown()


class Handler(BaseRequestHandler):
    addr = socket.getfqdn()

    def handle(self):
        data = self.request[0].strip()
        if data == b'THERMAL_REQ':
            # print("Detected client on %s" % (self.client_address))
            socket = self.request[1]
            reply = "THERMAL_DATA\n{}".format(json.dumps({'data': i2c_thread.get_data(), 'ambient' : i2c_thread.get_ambient_temp()}))
            socket.sendto(bytearray(reply, encoding='ascii'), self.client_address)


def initIRPack():
    global i2c_thread
    i2c_thread = IrI2c()
    if i2c_thread.start() is not None:
        i2c_thread.start()
    server = UDPServerThread()
    server.start()