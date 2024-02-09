import datetime
from datetime import time

from pyomyo import Myo, emg_mode


def worker_myo(q_out, q_terminate, q_myo_ready):
    m = None
    try:
        m = Myo(mode=emg_mode.FILTERED)
    except ValueError as e:
        print(e)
        # Add to terminate queue to stop the worker
        q_terminate.put(str(e))
        return None
    m.connect()

    def add_to_queue(emg, moving):
        # Get timestamp since epoch in milliseconds
        timestamp = datetime.datetime.now().timestamp() * 1000

        data = list(emg)
        data.append(timestamp)

        q_out.put(data)

    m.add_emg_handler(add_to_queue)

    def print_battery(bat):
        print("Battery level:", bat)

    m.add_battery_handler(print_battery)

    # Orange logo and bar LEDs
    m.set_leds([128, 0, 0], [128, 0, 0])
    # Vibrate to know we connected okay
    m.vibrate(1)

    q_myo_ready.put(True)

    """worker function"""
    while q_terminate.empty():
        m.run()

    print("Myo worker finished")