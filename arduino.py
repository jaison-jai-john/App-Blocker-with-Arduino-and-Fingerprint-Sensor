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
        return self.ser.readline().decode().lower()

    def wait_for(self, data=[]):
        while True and data != []:
            read = self.read()
            for d in data:
                if d.lower() in read:
                    return read

    def close(self):
        self.ser.close()
