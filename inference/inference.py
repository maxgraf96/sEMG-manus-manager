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
from constants import FEATURE_VECTOR_DIM
from inference.worker_inference import worker_myo_receiver, worker_inference_res_to_visualiser
from myo.worker_myo import worker_myo
from components.gesture_detail import show_visualisation


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
        top_frame.pack_configure(fill=tk.X, pady=10)
        tk.Label(top_frame, text="From File", font=(FONT, 16), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        self.browse_button = tk.Button(self, text="Select File", bg=self.root.colour_config["bg"],
                                       fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1,
                                       command=self.browse)
        self.browse_button.pack_configure(pady=10, ipady=5)

        self.file_label = tk.Label(self, text="File: ", bg=self.root.colour_config["bg"],
                                   fg=self.root.colour_config["fg"])
        self.file_label.pack_configure(pady=10, ipady=5, fill=tk.X)

        self.inference_button = tk.Button(self, text="Run Inference", command=self.run_inference_on_file,
                                          bg=self.root.colour_config["bg"],
                                          fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.inference_button.pack_configure(pady=20, ipady=5)

        self.browse_button.config(width=40)
        self.inference_button.config(width=40)

    def run_inference_on_file(self, filepath):
        print("Running inference on file " + self.file_label.cget("text"))

        # Open file and send data to the server
        with open(filepath, 'r') as file:
            send_data = {"from_file": True, "data": []}
            for line in file:
                line_data = line.strip().split(',')
                # Skip header line
                if "emg" in line_data[0]:
                    continue
                # Parse first FEATURE_VECTOR_DIM values as EMG data
                emg_data = [int(float(x)) for x in line_data[:FEATURE_VECTOR_DIM]]
                send_data["data"].append(emg_data)

            js = json.dumps(send_data).encode('utf-8')
            self.inference_frame.pub_socket.send(js)

            # Wait for the result
            result = self.inference_frame.sub_socket.recv()
            result = json.loads(result.decode("utf-8"))

            data = result["data"]
            shape = result["shape"]
            if shape[1] == 1:
                print("Inference socket clogged with real time data, skipping...")
                while shape[1] == 1:
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
        self.p_inference_visualiser_bridge = None
        self.p_myo = None
        self.p_myo_receiver = None
        self.q_myo = None
        self.q_myo_imu = None
        self.q_terminate = None
        self.q_myo_ready = None
        self.root = root
        self.inference_frame = inference_frame

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.should_terminate_live_inference = False

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack_configure(fill=tk.X, pady=10)
        tk.Label(top_frame, text="From Live Data", font=(FONT, 16), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        self.inference_button = tk.Button(self, text="Run Live Inference", command=self.infer,
                                          bg=self.root.colour_config["bg"],
                                          fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.inference_button.pack_configure(pady=10, ipady=5, anchor=tk.CENTER)
        self.stop_inference_button = tk.Button(self, text="Stop Live Inference", command=self.stop_inference,
                                                  bg=self.root.colour_config["bg"],
                                                  fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)
        self.stop_inference_button.pack_configure(pady=10, ipady=5)

        self.inference_button.config(width=40)
        self.stop_inference_button.config(width=40)


    def check_terminate_live_inference(self):
        if self.should_terminate_live_inference:
            print("Terminating live inference")
            self.should_terminate_live_inference = False
            self.q_terminate.put(True)

            self.p_myo.join(1000)
            self.p_myo_receiver.join(1000)
            self.p_inference_visualiser_bridge.join(1000)

    def infer(self):
        print("Infer from live data")

        self.q_myo = multiprocessing.Queue()
        self.q_myo_imu = multiprocessing.Queue()
        self.q_terminate = multiprocessing.Queue()
        self.q_myo_ready = multiprocessing.Queue()

        # Many myo data collection process - same as in data_collection.py
        self.p_myo = multiprocessing.Process(target=worker_myo, args=(self.q_myo, self.q_myo_imu, self.q_terminate, self.q_myo_ready, ))
        # Custom myo receiver process
        self.p_myo_receiver = multiprocessing.Process(target=worker_myo_receiver, args=(self.q_myo, self.q_myo_imu, self.q_terminate, ))
        self.p_inference_visualiser_bridge = multiprocessing.Process(target=worker_inference_res_to_visualiser, args=(self.q_terminate, ))

        self.p_myo.start()
        self.p_myo_receiver.start()
        self.p_inference_visualiser_bridge.start()

        repeating_timer = helpers.RepeatedTimer(0.1, self.check_terminate_live_inference)

        # Visualiser to front
        show_visualisation()

    def stop_inference(self):
        self.should_terminate_live_inference = True




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
