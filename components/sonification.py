import math
import multiprocessing
import time
import tkinter as tk
from queue import Queue
from tkinter import ttk

import helpers
from config import FONT
from constants import DATA_LEN
from myo.worker_myo import worker_myo


def worker_myo_receiver_soni(q_myo, q_myo_imu, q_terminate):
    """
    Receive processed myo data and send it to INFERENCE
    :param q_myo: sEMG signals
    :param q_terminate:
    :return:
    """
    last_imu = None

    while q_terminate.empty():
        while not q_myo.empty():
            # print("Myo data: ", q_myo.get())

            emg_data = q_myo.get()[:8]
            # while not q_myo_imu.empty():
            #     last_imu = q_myo_imu.get()[:10]
            # emg_data.extend(last_imu)

            # Do sonification here
            print(emg_data)

            continue

        time.sleep(0.001)

    # Finish the process
    print("Myo sonification worker finished.")

class SonificationFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.p_myo = None
        self.p_myo_receiver = None
        self.q_myo = None
        self.q_myo_imu = None
        self.q_terminate = None
        self.q_myo_ready = None

        self.running = False
        self.should_terminate_sonification = False

        self.width = 200
        self.height = 400
        self.center_y = self.height // 2

        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg='white')
        self.canvas.pack()

        self.signal_line = None
        self.time = 0
        self.speed = 0.1
        self.amplitude = 100
        self.frequency = 1

        self.points = []
        for i in range(self.width):
            y = 0
            self.points.append(y)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Sonification", font=(FONT, 20), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        # Create frame for the main content
        main_frame = tk.Frame(self, name="testoo", bg=self.root.colour_config["bg"])

        # Add button to start live sonification
        self.start_button = tk.Button(main_frame, text="Start Live Sonification", command=self.toggle_live_sonification)
        # Center the button
        self.start_button.config(width=40)
        self.start_button.pack_configure(pady=10, ipady=5, anchor=tk.CENTER)

        # Pack the frame
        main_frame.pack_configure(fill='both', expand=False, anchor='nw', padx=20, pady=20)
        #Frame padding 20 px

    def myo_callback_loop(self):

        # Get q_myo size and replace points accordingly
        size = self.q_myo.qsize()
        for i in range(size):
            y = self.q_myo.get()[0] # TODO add other EMG channels
            # Remove oldest item from list
            self.points.pop(0)
            # Add new item
            self.points.append(y)

        self.update_signal()

        if self.should_terminate_sonification:
            print("Terminating live sonification")
            self.repeating_timer.stop()
            self.should_terminate_sonification = False
            self.q_terminate.put(True)

            self.p_myo.join(1000)
            # self.p_myo_receiver.join(1000)

    def toggle_live_sonification(self):
        self.running = not self.running
        if not self.running:
            # Update button text
            self.start_button.config(text="Start Live Sonification")
            self.should_terminate_sonification = True
            return
        else:
            self.start_button.config(text="Stop Live Sonification")

        # Start sonification
        self.q_myo = multiprocessing.Queue()
        self.q_myo_imu = multiprocessing.Queue()
        self.q_terminate = multiprocessing.Queue()
        self.q_myo_ready = multiprocessing.Queue()

        # Many myo data collection process - same as in data_collection.py
        self.p_myo = multiprocessing.Process(target=worker_myo,
                                             args=(self.q_myo, self.q_myo_imu, self.q_terminate, self.q_myo_ready,))
        # Custom myo receiver process
        self.p_myo_receiver = multiprocessing.Process(target=worker_myo_receiver_soni,
                                                      args=(self.q_myo, self.q_myo_imu, self.q_terminate,))

        self.p_myo.start()
        # self.p_myo_receiver.start()

        self.repeating_timer = helpers.RepeatedTimer(0.05, self.myo_callback_loop)

    def update_signal(self):
        self.canvas.delete("line")

        for i in range(len(self.points) - 1):
            self.canvas.create_line(
                i,
                self.center_y + self.points[i],
                i + 1,
                self.center_y + self.points[i + 1],
                fill="blue",
                tags="line")

