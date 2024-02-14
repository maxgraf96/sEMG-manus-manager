import json
import multiprocessing
import os
import time
import tkinter as tk
from tkinter.filedialog import askopenfilename

import numpy as np
import zmq

import helpers
from components import gesture_detail
from config import FONT
from myo.worker_myo import worker_myo


class InferenceFromFile(tk.Frame):
    def __init__(self, parent, root, inference_frame):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.browse_button = None
        self.inference_button = None
        self.file_label = None
        self.root = root
        self.inference_frame = inference_frame

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def browse(self):
        f_path = askopenfilename(initialdir="./user_data",
                                 title="Select File", filetypes=(("CSV Files", "*.csv*"), ("All Files", "*.*")))

        self.load_file(f_path)

    def load_file(self, file_path):
        if file_path:
            # Got file
            # Take only filename
            if "/" in file_path:
                filename = file_path.split("/")[-1]
            elif "\\" in file_path:
                filename = file_path.split("\\")[-1]
            self.file_label.configure(text="File Opened: " + filename)

            self.run_inference_on_file(file_path)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="File", font=(FONT, 16), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        self.browse_button = tk.Button(self, text="Select File", bg=self.root.colour_config["bg"],
                                       fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1,
                                       command=self.browse)
        self.browse_button.pack_configure(pady=10, ipady=5, fill=tk.X)

        self.file_label = tk.Label(self, text="File: ", bg=self.root.colour_config["bg"],
                                   fg=self.root.colour_config["fg"])
        self.file_label.pack_configure(pady=10, ipady=5, fill=tk.X)

        self.inference_button = tk.Button(self, text="Run Inference", command=self.run_inference_on_file,
                                          bg=self.root.colour_config["bg"],
                                          fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.inference_button.pack_configure(pady=20, ipady=5, fill=tk.X)

    def run_inference_on_file(self, filepath):
        print("Running inference on file " + self.file_label.cget("text"))

        # Open file and send data to the server
        with open(filepath, 'r') as file:
            send_data = {"from_file": True, "data": []}
            for line in file:
                line_data = line.strip().split(',')
                # Parse first 8 values as EMG data
                emg_data = [int(float(x)) for x in line_data[:8]]
                send_data["data"].append(emg_data)

            js = json.dumps(send_data).encode('utf-8')
            self.inference_frame.pub_socket.send(js)

            # Wait for the result
            result = self.inference_frame.sub_socket.recv()
            result = json.loads(result.decode("utf-8"))

            data = result["data"]
            shape = result["shape"]
            print("Received inference result with shape:", shape)

            data = np.array(data).reshape(shape)

            # Convert data to temp CSV
            temp_csv_path = helpers.create_visualiser_csv(data)
            helpers.update_visualiser_temp_file(temp_csv_path)

            gesture_detail.show_visualisation()


class InferenceFromLive(tk.Frame):
    def __init__(self, parent, root, inference_frame):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root
        self.inference_frame = inference_frame

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="From Live Data", font=(FONT, 16), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        self.inference_button = tk.Button(self, text="Run Live Inference", command=self.infer,
                                          bg=self.root.colour_config["bg"],
                                          fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.inference_button.pack_configure(pady=10, ipady=5, fill=tk.X)

    def infer(self):
        print("Infer from live data")

        q_myo = multiprocessing.Queue()
        q_terminate = multiprocessing.Queue()
        q_myo_ready = multiprocessing.Queue()

        p_myo = multiprocessing.Process(target=worker_myo, args=(q_myo, q_terminate, q_myo_ready,))
        p_myo.start()

        # Wait for myo to be ready
        while q_myo_ready.empty():
            time.sleep(0.01)

        # Ready and getting data
        while True:
            if not q_myo.empty():
                emg_data = q_myo.get()[:8]
                send_data = {"from_file": False, "data": emg_data}
                js = json.dumps(send_data).encode('utf-8')
                self.inference_frame.pub_socket.send(js)
                continue
            else:
                time.sleep(0.01)


        p_myo.join(100)


class InferenceFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root

        self.inference_from_file = None
        self.inference_from_live = None

        # Global zmq context
        self.context = zmq.Context()
        self.pub_topic = "emg_data"
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://127.0.0.1:55510")

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://127.0.0.1:55511")
        self.sub_socket.subscribe("")

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Inference", font=(FONT, 20), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        # Create two frames for the two columns
        left_frame = tk.Frame(self, name="testoo", bg=self.root.colour_config["bg"])
        right_frame = tk.Frame(self, bg=self.root.colour_config["bg"])

        # Left frame is inference from file, right frame is inference from live data
        self.inference_from_file = InferenceFromFile(left_frame, self.root, self)
        self.inference_from_file.pack(fill='both', expand=True)

        self.inference_from_live = InferenceFromLive(right_frame, self.root, self)
        self.inference_from_live.pack(fill='both', expand=True)

        # Pack the frames side by side
        left_frame.pack(side='left', fill='both', expand=True)
        right_frame.pack(side='right', fill='both', expand=True)

    def switch_to_inference_from_file(self, file_path):
        # self.root.notebook.select(1)
        self.inference_from_file.load_file(file_path)
