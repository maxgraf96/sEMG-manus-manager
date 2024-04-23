import datetime
import multiprocessing
import os
import signal
import socket
import subprocess
import time
import tkinter as tk
import tkinter.messagebox as msgbox
from tkinter import LEFT, ttk

import numpy as np
import send2trash

import helpers
from components.browser import BrowserFrame
from components.emg_inspector import EMGInspectorWindow
from config import FONT, VISUALISER_PATH
from constants import XRMI_GESTURES, DATA_CSV_HEADER_STR
from helpers import RepeatedTimer
from networking import netz_connector
from myo.data_collection import start_recording

# Visualiser setup -> that's the Three.js app
# Queue for interacting with the visualiser
q_visualiser = multiprocessing.Queue()
# Visualiser process
p_visualiser = None

# Browser setup
is_browser_open = False
browser_window = None
browser_frame = None

# Inspector setup
emg_inspector_window = None

# Myo setup
q_myo = multiprocessing.Queue()
q_myo_imu = multiprocessing.Queue()

# MANUS setup
q_manus = multiprocessing.Queue()

# Global socket for Unity communication

unity_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
unity_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
interfaces = socket.getaddrinfo(
    host=socket.gethostname(), port=None, family=socket.AF_INET
)
allips = [ip[-1][0] for ip in interfaces]
# allips.append("127.0.0.1")


def visualiser_process(q_visualiser):
    # Run the visualiser: the command is 'npm run dev' and the working directory is the visualiser path
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=VISUALISER_PATH,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        shell=True,
    )

    # Wait for the visualiser to be ready
    while q_visualiser.empty():
        time.sleep(0.3)

    # Send ctrl+c and y to the visualiser process
    proc.send_signal(signal.CTRL_BREAK_EVENT)
    time.sleep(0.1)
    proc.send_signal(signal.CTRL_BREAK_EVENT)

    proc.kill()

    return


def open_browser_window(url):
    # Create a new top-level window
    global browser_window, browser_frame
    browser_window = tk.Toplevel()
    browser_window.title("Hand Visualiser")
    browser_window.minsize(800, 600)

    # Create a WebFrame in the new window
    browser_window.grid_columnconfigure(0, weight=1)
    browser_window.grid_rowconfigure(0, weight=1)

    # Create Frame
    frame = tk.Frame(browser_window, bg="black")
    frame.grid(row=0, column=0, sticky=("NSWE"))

    # Create Browser Frame
    browser_frame = BrowserFrame(frame)
    browser_frame.pack(fill=tk.BOTH, expand=tk.YES)

    # add callback for when the window is closed
    browser_window.protocol("WM_DELETE_WINDOW", lambda: on_browser_window_close())

    # Load the URL
    browser_frame.embed_browser(url)


def show_visualisation():
    """
    Show the visualisation for the selected recording
    :return:
    """

    global p_visualiser, q_visualiser, is_browser_open, browser_window
    # Check if the visualiser process is already running
    if p_visualiser is None:
        print("No visualiser process running, starting a new one.")
        p_visualiser = multiprocessing.Process(
            target=visualiser_process, args=(q_visualiser,)
        )
        p_visualiser.start()

    if not is_browser_open:
        # Open the visualiser in a new browser window
        open_browser_window("http://localhost:5173")
        # Set the flag to indicate that the browser window is open
        is_browser_open = True
    else:
        # Refresh the visualiser
        # Just reload the page
        browser_frame.reload_page()
        # push browser to front
        browser_window.lift()
        return


class GestureDetail(tk.Frame):
    def __init__(self, parent, user_id, session_id, gesture, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.user_id = user_id
        self.session_id = session_id
        self.gesture = gesture
        self.root = root

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create a context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(
            label="Show in Explorer", command=self.show_in_explorer
        )
        self.context_menu.add_command(
            label="Show 3D Visualisation", command=self.show_visualisation
        )
        self.context_menu.add_command(
            label="Run Inference on File", command=self.run_inference_on_file
        )
        self.context_menu.add_command(
            label="Open Inspector", command=self.open_inspector
        )

    def on_right_click(self, event):
        # Get the index of the item under the cursor
        try:
            index = self.recordings_listbox.nearest(event.y)
            self.recordings_listbox.select_clear(0, tk.END)
            self.recordings_listbox.select_set(index)
        except Exception as e:
            print(e)
            return

        # Show the context menu
        self.context_menu.post(event.x_root, event.y_root)

    def show_in_explorer(self):
        # Get the normalised path
        normalized_path = self.get_normalised_path()
        # Open the file location in Windows Explorer
        subprocess.run(["explorer", "/select,", normalized_path])

    def create_widgets(self):
        tk.Label(
            self,
            text=f"Gesture {self.gesture}",
            font=(FONT, 14),
            bg=self.root.colour_config["bg"],
            fg=self.root.colour_config["fg"],
        ).pack()

        self.recordings_listbox = tk.Listbox(
            self,
            height=7,
            fg=self.root.colour_config["fg"],
            bg=self.root.colour_config["bg"],
            selectbackground="grey",
            selectforeground="white",
            highlightthickness=0,
            highlightbackground="grey",
            relief=tk.RIDGE,
            borderwidth=1,
        )
        self.recordings_listbox.pack(fill=tk.BOTH)
        self.recordings_listbox.bind("<Delete>", self.delete_recording_listbox)
        self.recordings_listbox.bind("<Button-3>", self.on_right_click)

        # On left click, open the selected recording
        self.recordings_listbox.bind(
            "<Button-1>", lambda event: self.open_inspector_if_open()
        )

        self.user_cancelled = False

        # Load sessions for this gesture
        self.load_recordings()

        self.slow_recording_button = tk.Button(
            self,
            text="Record Slow",
            command=lambda: self.start_new_recording("slow"),
            bg="#95a5a6",
            fg=self.root.colour_config["fg"],
            relief=tk.RIDGE,
            borderwidth=1,
        )
        # New session button should be 200px wide and left-aligned
        self.slow_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))
        self.medium_recording_button = tk.Button(
            self,
            text="Record Medium",
            command=lambda: self.start_new_recording("medium"),
            bg="#bdc3c7",
            fg=self.root.colour_config["fg"],
            relief=tk.RIDGE,
            borderwidth=1,
        )
        self.medium_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))

        self.fast_recording_button = tk.Button(
            self,
            text="Record Fast",
            command=lambda: self.start_new_recording("fast"),
            bg="#ecf0f1",
            fg=self.root.colour_config["fg"],
            relief=tk.RIDGE,
            borderwidth=1,
        )
        self.fast_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))
        self.stop_recording_button = tk.Button(
            self,
            text="Stop Recording",
            command=self.stop_recording,
            bg="#e74c3c",
            fg=self.root.colour_config["fg"],
            relief=tk.RIDGE,
            borderwidth=1,
        )
        self.stop_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))
        # Hide button by default
        self.stop_recording_button.pack_forget()

        self.progressbar = ttk.Progressbar(
            self, orient=tk.HORIZONTAL, length=200, mode="determinate"
        )
        # Hide the progress bar
        self.progressbar.pack_forget()

    def load_recordings(self):
        # Get the session folder path
        gesture_folder = os.path.join(
            "user_data",
            f"u_{self.user_id}",
            f"s_{self.session_id}",
            f"g_{self.gesture}",
        )

        # Clear the existing recordings listbox
        self.recordings_listbox.delete(0, tk.END)

        # Check if the session folder exists
        if not os.path.exists(gesture_folder):
            return

        # Find all CSV files in the session folder
        recording_files = [
            f
            for f in os.listdir(gesture_folder)
            if os.path.isfile(os.path.join(gesture_folder, f)) and f.endswith(".csv")
        ]

        # For each recording file, extract information and add it to the listbox
        for recording_file in recording_files:
            # Extract the filename
            filename = recording_file.split(".csv")[0]

            # Add the recording information to the listbox
            # You can modify this to display additional information from the CSV file
            self.recordings_listbox.insert(tk.END, f"{filename}")

        # Bind double-click event to open the selected recording
        self.recordings_listbox.bind(
            # "<Double-Button-1>", lambda event: self.show_visualisation()
            "<Double-Button-1>",
            lambda event: self.open_selected_recording(),
        )

    def show_visualisation(self):
        filename = (
            self.recordings_listbox.get(self.recordings_listbox.curselection()[0])
            + ".csv"
        )
        # Get full absolute path
        filename = os.path.join(
            "user_data",
            f"u_{self.user_id}",
            f"s_{self.session_id}",
            f"g_{self.gesture}",
            filename,
        )

        # Extract hand pose data from the selected recording - this must be in the same format as the inference results.
        data = helpers.extract_hand_pose_data_from_gt_csv(filename)
        # Create visualiser temp csv
        temp_csv_path = helpers.create_visualiser_csv(data)

        # Copy file to the visualiser folder
        helpers.update_visualiser_temp_file(temp_csv_path)
        show_visualisation()

    def open_selected_recording(self):
        """
        Open the selected recording in the default application (Excel)
        :return:
        """
        # Get the selected recording index
        selected_index = self.recordings_listbox.curselection()
        # Check if a recording is selected
        if not selected_index:
            return
        # Get the session folder path
        session_folder = os.path.join(
            "user_data",
            f"u_{self.user_id}",
            f"s_{self.session_id}",
            f"g_{self.gesture}",
        )
        # Get the selected filename
        selected_filename = self.recordings_listbox.get(selected_index[0]) + ".csv"
        # Open the selected recording file
        os.startfile(os.path.join(session_folder, selected_filename))

    def start_new_recording(self, speed: str = "medium"):
        # Show stop recording button
        self.stop_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))
        self.user_cancelled = False

        # If we're doing XRMI gestures we need to notify Netz
        if self.gesture in XRMI_GESTURES:
            # Message content is the name of the gesture (self.gesture)
            message = self.gesture.encode("utf-8")

            for ip in allips:
                print(f"sending on {ip}")
                sock = socket.socket(
                    socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
                )  # UDP
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind((ip, 0))
                sock.sendto(message, ("255.255.255.255", 11000))
                sock.close()

            # Sleep for a bit until Unity got the message
            time.sleep(1)

        # Helper q to terminate the recording
        self.q_terminate = multiprocessing.Queue()
        # Helper q to check if the myo is ready
        # Only when the myo is ready, the recording will start
        q_myo_ready = multiprocessing.Queue()

        # Clear all queues
        q_myo.empty()
        q_myo_imu.empty()
        q_manus.empty()

        # Start a new recording
        start_recording(q_myo, q_myo_imu, q_manus, self.q_terminate, q_myo_ready)

        # Wait for myo to be ready
        while q_myo_ready.empty() and self.q_terminate.empty():
            time.sleep(0.01)

        # Colour background of the status bar to indicate that the recording is in progress
        self.root.status_bar.config(bg="#EA2027")

        # Show progress bar
        self.progressbar["value"] = 0
        self.progressbar.pack_configure(pady=(5, 0))

        # Start the recording
        RECORDING_LENGTH = 10
        WARMUP_LENGTH = 1
        # MYO_SR = 50
        MYO_SR = 200

        q_netz_finished = multiprocessing.Queue()

        # Open lambda new thread to check if Netz sent the recording finished signal
        if self.gesture in XRMI_GESTURES:
            p = multiprocessing.Process(
                target=netz_connector.listen_for_netz_finished_process,
                args=(q_netz_finished,),
            )
            p.start()

        if self.gesture == "melody":
            # Longer recording for melody
            RECORDING_LENGTH = 20

        def check_terminate():
            if not self.user_cancelled:
                # Update progress bar
                self.progressbar["value"] = (
                    q_myo.qsize() / (MYO_SR * (WARMUP_LENGTH + RECORDING_LENGTH)) * 100
                )

                if self.gesture in XRMI_GESTURES:
                    # Check if Netz sent the recording finished signal
                    if q_netz_finished.empty():
                        return
                else:
                    # Normal, check if the recording time is up
                    if q_myo.qsize() < MYO_SR * (WARMUP_LENGTH + RECORDING_LENGTH):
                        return

            # Stop timer
            repeating_timer.stop()

            # Terminate the recording
            self.q_terminate.put(True)

            # Get data from our queues
            emg_data = []
            imu_data = []
            manus_data = []

            while not q_myo.empty():
                current = q_myo.get()
                emg_data.append(current)

            while not q_myo_imu.empty():
                current = q_myo_imu.get()
                imu_data.append(current)

            while not q_manus.empty():
                current = q_manus.get()
                manus_data.append(current)

            # Now, for each data point in q_myo find the corresponding data point in q_manus - the one with
            # the closest timestamp
            recording = []
            time_diffs_myo_imu = []
            time_diffs_myo_manus = []
            for emg in emg_data:
                timestamp = emg[-1]

                # Find the closest timestamp in the imu data
                closest_imu = min(imu_data, key=lambda x: abs(x[-1] - timestamp))
                time_diffs_myo_imu.append(abs(closest_imu[-1] - timestamp))

                # Find the closest timestamp in the manus data
                closest_manus = min(manus_data, key=lambda x: abs(x[-1] - timestamp))
                time_diffs_myo_manus.append(abs(closest_manus[-1] - timestamp))

                recording.append(emg[:-1] + closest_imu[:-1] + closest_manus[:-1])

            # Ditch the first 1s of data points (warmup)
            recording = recording[MYO_SR:]

            print(
                f"Matched {len(recording)} EMG data points with {len(manus_data)} hand pose samples."
            )
            avg_time_diff_imu = float("{:.2f}".format(np.mean(time_diffs_myo_imu)))
            avg_time_diff_manus = float("{:.2f}".format(np.mean(time_diffs_myo_manus)))
            print(f"Average time difference myo-imu: {avg_time_diff_imu} ms")
            print(f"Average time difference myo-manus: {avg_time_diff_manus} ms")

            # Colour background of the status bar to indicate that the recording is finished
            self.root.status_bar.config(bg=self.root.status_bar_bg)

            # Save recording if it's not empty
            if recording and not self.user_cancelled:
                # Generate a unique filename for the recording
                now = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
                recording_filename = f"recording_{speed}_{now}.csv"
                # Get the session folder path
                session_folder = os.path.join(
                    "user_data",
                    f"u_{self.user_id}",
                    f"s_{self.session_id}",
                    f"g_{self.gesture}",
                )
                # Create the recording file
                recording_path = os.path.join(session_folder, recording_filename)
                os.makedirs(session_folder, exist_ok=True)

                np.savetxt(
                    recording_path,
                    np.array(recording, dtype=float),
                    delimiter=",",
                    header=DATA_CSV_HEADER_STR,
                )
                # Display a confirmation message
                msgbox.showinfo(
                    "Recording Finished", f"Recording saved as {recording_filename}"
                )
            else:
                if self.user_cancelled:
                    # User cancelled the recording -> display a message
                    msgbox.showinfo("Recording Cancelled", "Recording was cancelled.")
                else:
                    # Retrieve error string from q_terminate (2nd element in the queue)
                    error = self.q_terminate.get()
                    # Recording empty -> display error dialog box
                    msgbox.showerror("Recording Error", error)

            # Hide progress bar
            self.progressbar.pack_forget()
            # Update the recordings listbox
            self.load_recordings()
            # Update total number of datapoints
            self.root.update_total_datapoints()
            # Hide the stop recording button
            self.stop_recording_button.pack_forget()
            self.user_cancelled = False

        # Start a repeating timer to check if the recording is finished
        repeating_timer = RepeatedTimer(0.1, check_terminate)

    def stop_recording(self):
        # Terminate the recording
        self.q_terminate.put(True)
        self.user_cancelled = True

    def get_normalised_path(self):
        # Get the selected recording index
        selected_index = self.recordings_listbox.curselection()
        # Check if a recording is selected
        if not selected_index:
            return None
        # Get the session folder path
        session_folder = os.path.join(
            "user_data",
            f"u_{self.user_id}",
            f"s_{self.session_id}",
            f"g_{self.gesture}",
        )
        # Get the selected filename
        selected_filename = self.recordings_listbox.get(selected_index[0]) + ".csv"
        # Create full path
        selected_filename = os.path.join(session_folder, selected_filename)
        # Normalize the file path
        normalized_path = os.path.normpath(selected_filename)
        return normalized_path

    def delete_recording_listbox(self, event):
        # Get selected item index
        selected_index = self.recordings_listbox.curselection()
        if selected_index:
            selected_filename = self.recordings_listbox.get(selected_index[0]) + ".csv"
            # Ask for confirmation
            if msgbox.askyesno(
                "Delete recording for gesture",
                f"Are you sure you want to delete recording {selected_filename}?",
            ):
                # Delete the csv file
                session_folder = os.path.join(
                    "user_data",
                    f"u_{self.user_id}",
                    f"s_{self.session_id}",
                    f"g_{self.gesture}",
                )
                send2trash.send2trash(os.path.join(session_folder, selected_filename))
                # os.remove(os.path.join(session_folder, selected_filename))

                # Delete the selected item from listbox
                self.recordings_listbox.delete(selected_index[0])

                self.load_recordings()

    def run_inference_on_file(self):
        # Get the normalised path
        normalized_path = self.get_normalised_path()

        # Switch to inference tab and pass the file path
        self.root.switch_to_inference_from_file(normalized_path)

    def open_inspector(self):
        global emg_inspector_window

        # Get the normalised path
        normalized_path = self.get_normalised_path()

        if emg_inspector_window is None:
            emg_inspector_window = EMGInspectorWindow(normalized_path, self.root)
            # Add on close lambda to reset the window
            emg_inspector_window.protocol(
                "WM_DELETE_WINDOW", lambda: self.on_inspector_window_close()
            )
        else:
            emg_inspector_window.load_file(normalized_path)

    def on_inspector_window_close(self):
        global emg_inspector_window
        if emg_inspector_window:
            emg_inspector_window.destroy()
            emg_inspector_window = None

    def open_inspector_if_open(self):
        global emg_inspector_window
        if emg_inspector_window is not None:
            self.open_inspector()


def on_browser_window_close():
    global is_browser_open, browser_window, browser_frame
    if browser_frame:
        browser_frame.on_root_close()
        browser_frame = None
    if browser_window:
        browser_window.destroy()
        browser_window = None

    # Reset the flag to indicate that the browser window is closed
    is_browser_open = False


def get_browser_open():
    global is_browser_open
    return is_browser_open
