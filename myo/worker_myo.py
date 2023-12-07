from pyomyo import Myo, emg_mode


def worker_myo(q_out, q_terminate, q_myo_ready):
    m = Myo(mode=emg_mode.PREPROCESSED)
    m.connect()

    def add_to_queue(emg, movement):
        q_out.put(emg)

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