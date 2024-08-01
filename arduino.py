import serial

from variables import reading


class Arduino:
    def __init__(self, port, baudrate, timeout=1):
        """
        Initialize the Arduino object

        :param port: the port to connect to
        :param baudrate: the baudrate to use
        :param timeout: the timeout for the connection
        """
        # PORT of the arduino COM12
        self.port = port
        # set the baudrate
        self.baudrate = baudrate
        # set the timeout
        self.timeout = timeout
        # create a serial connection
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def write(self, data):
        # write data to the serial connection
        self.ser.write(data.encode())

    def read(self):
        # read data from the serial connection
        return self.ser.readline().decode().lower()

    def stop_reading(self):
        # stop reading from the serial connection
        reading[0] = False

    def start_reading(self):
        # start reading from the serial connection
        reading[0] = True

    def wait_for(self, data=[]):
        # wait for data to be read from the serial connection
        while True and data != []:
            # check if reading flag is false
            if not reading[0]:
                # stop reading
                break
            # read the data
            read = self.read()
            # check if data is in the read data
            for d in data:
                # check if data is in the read data
                if d.lower() in read:
                    # return the read data
                    return read
        return "stopped reading"

    def close(self):
        # close the serial connection
        self.ser.close()
