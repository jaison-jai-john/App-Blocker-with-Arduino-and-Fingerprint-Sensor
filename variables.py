reading = [True]
kill = False
checked = []


def stop_reading():
    global reading
    reading = False


def start_reading():
    global reading
    reading = True


def kill_all():
    global kill
    kill = True
