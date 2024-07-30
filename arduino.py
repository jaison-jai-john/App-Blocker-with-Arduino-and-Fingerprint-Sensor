import serial


class Arduino:
    def __init__(self, port, baudrate, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def write(self, data):
        self.ser.write(data.encode())

    def read(self):
        return self.ser.readline().decode()

    def wait_for(self, data=[]):
        while True:
            read = self.read()
            if any([r in read for r in data]):
                return read

    def close(self):
        self.ser.close()
