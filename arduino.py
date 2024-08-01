import serial

from variables import reading


class Arduino:
    def __init__(self, port, baudrate, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def write(self, data):
        self.ser.write(data.encode())

    def read(self):
        return self.ser.readline().decode().lower()

    def stop_reading(self):
        reading[0] = False

    def start_reading(self):
        reading[0] = True

    def wait_for(self, data=[]):
        while True and data != []:
            if not reading[0]:
                break
            read = self.read()
            for d in data:
                if d.lower() in read:
                    return read
        return "stopped reading"

    def close(self):
        self.ser.close()
