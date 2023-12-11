import multiprocessing
import os
import signal
import subprocess
import time
import tkinter as tk
import tkinter.messagebox as msgbox
import webbrowser
from tkinter import LEFT, RIGHT
import datetime

import numpy as np
import send2trash

from components.browser import BrowserFrame
from myo.data_collection import start_recording
from config import FONT, VISUALISER_PATH

GESTURES = ['fist', 'wave_in', 'wave_out', 'fingers_spread', 'double_tap']

# Visualiser setup -> that's the Three.js app
# Queue for interacting with the visualiser
q_visualiser = multiprocessing.Queue()
# Visualiser process
p_visualiser = None

# Browser setup
is_browser_open = False
browser_window = None
browser_frame = None


def visualiser_process(q):
    # Run the visualiser: the command is 'npx vite' and the working directory is the visualiser path
    proc = subprocess.Popen(['npx.cmd', 'vite'],
                            cwd=VISUALISER_PATH,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                            )

    # Wait for the visualiser to be ready
    while q.empty():
        time.sleep(0.5)

    # Send ctrl+c and y to the visualiser process
    proc.send_signal(signal.CTRL_BREAK_EVENT)
    time.sleep(0.1)

    proc.kill()

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
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
        self.context_menu.add_command(label="Show Visualisation", command=self.show_visualisation)

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
        # Get the selected recording index
        selected_index = self.recordings_listbox.curselection()
        # Check if a recording is selected
        if not selected_index:
            return
        # Get the session folder path
        session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}', f'g_{self.gesture}')
        # Get the selected filename
        selected_filename = self.recordings_listbox.get(selected_index[0]) + '.csv'
        # Create full path
        selected_filename = os.path.join(session_folder, selected_filename)
        # Normalize the file path
        normalized_path = os.path.normpath(selected_filename)
        # Open the file location in Windows Explorer
        subprocess.run(['explorer', '/select,', normalized_path])

    def create_widgets(self):
        tk.Label(self, text=f"Gesture {self.gesture}", font=(FONT, 14), bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]).pack()

        self.recordings_listbox = tk.Listbox(self, height=7,
                                             fg=self.root.colour_config["fg"],
                                             bg=self.root.colour_config["bg"],
                                             selectbackground='grey',
                                             selectforeground='white',
                                             highlightthickness=0, highlightbackground='grey',
                                             relief=tk.RIDGE, borderwidth=1)
        self.recordings_listbox.pack(fill=tk.BOTH)
        self.recordings_listbox.bind("<Delete>", self.delete_recording_listbox)
        self.recordings_listbox.bind("<Button-3>", self.on_right_click)

        # Load sessions for this gesture
        self.load_recordings()

        self.new_recording_button = tk.Button(self, text="Start New Recording", command=self.start_new_recording,
                                              bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"],
                                              relief=tk.RIDGE, borderwidth=1)
        # New session button should be 200px wide and left-aligned
        self.new_recording_button.pack_configure(side=LEFT, ipadx=30, pady=(5, 0))

    def load_recordings(self):
        # Get the session folder path
        gesture_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}', f'g_{self.gesture}')

        # Clear the existing recordings listbox
        self.recordings_listbox.delete(0, tk.END)

        # Check if the session folder exists
        if not os.path.exists(gesture_folder):
            return

        # Find all CSV files in the session folder
        recording_files = [f for f in os.listdir(gesture_folder) if
                           os.path.isfile(os.path.join(gesture_folder, f)) and f.endswith('.csv')]

        # For each recording file, extract information and add it to the listbox
        for recording_file in recording_files:
            # Extract the filename
            filename = recording_file.split('.csv')[0]

            # Add the recording information to the listbox
            # You can modify this to display additional information from the CSV file
            self.recordings_listbox.insert(tk.END, f"{filename}")

        # Bind double-click event to open the selected recording
        self.recordings_listbox.bind(
            "<Double-Button-1>", lambda event: self.show_visualisation()
            # "<Double-Button-1>", lambda event: self.open_selected_recording()
        )

    def show_visualisation(self):
        """
        Show the visualisation for the selected recording
        :return:
        """

        global p_visualiser, is_browser_open, q_visualiser
        # Check if the visualiser process is already running
        if p_visualiser is not None:
            # Pipe the filename to the visualiser
            filename = self.recordings_listbox.get(self.recordings_listbox.curselection()[0]) + '.csv'
            print(f"Visualiser already running, piping new file {filename}.")
            # TODO update this with the actual hand data
        else:
            print("No visualiser process running, starting a new one.")
            p_visualiser = multiprocessing.Process(target=visualiser_process,
                                               args=(q_visualiser,))
            p_visualiser.start()

        if not is_browser_open:
            # Open the visualiser in a new browser window
            self.open_browser_window("http://localhost:5173")
            # Set the flag to indicate that the browser window is open
            is_browser_open = True
        else:
            # Refresh the visualiser
            # TODO
            return

    def on_browser_window_close(self):
        global is_browser_open, browser_window, browser_frame
        if browser_frame:
            browser_frame.on_root_close()
            browser_frame = None
        if browser_window:
            browser_window.destroy()
            browser_window = None

        # Reset the flag to indicate that the browser window is closed
        is_browser_open = False

    def open_browser_window(self, url):
        # Create a new top-level window
        global browser_window, browser_frame
        browser_window = tk.Toplevel()
        browser_window.title("Hand Visualiser")
        browser_window.minsize(800, 600)

        # Create a WebFrame in the new window
        browser_window.grid_columnconfigure(0, weight=1)
        browser_window.grid_rowconfigure(0, weight=1)

        # Create Frame
        frame = tk.Frame(browser_window, bg='black')
        frame.grid(row=0, column=0, sticky=('NSWE'))

        # Create Browser Frame
        browser_frame = BrowserFrame(frame)
        browser_frame.pack(fill=tk.BOTH, expand=tk.YES)

        # add callback for when the window is closed
        browser_window.protocol("WM_DELETE_WINDOW", lambda: self.on_browser_window_close())

        # Load the URL
        browser_frame.embed_browser(url)

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
        session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}', f'g_{self.gesture}')
        # Get the selected filename
        selected_filename = self.recordings_listbox.get(selected_index[0]) + '.csv'
        # Open the selected recording file
        os.startfile(os.path.join(session_folder, selected_filename))

    def start_new_recording(self):
        q_result = multiprocessing.Queue()
        # Helper q to terminate the recording
        q_terminate = multiprocessing.Queue()
        # Helper q to check if the myo is ready
        # Only when the myo is ready, the recording will start
        q_myo_ready = multiprocessing.Queue()

        # Start a new recording
        start_recording(q_result, q_terminate, q_myo_ready)

        # Record for 5 seconds
        should_stop_recording = False
        recording = []
        while q_myo_ready.empty():
            time.sleep(0.01)

        timer = time.time()
        while not should_stop_recording:
            while not q_result.empty():
                emg = q_result.get()
                # Convert the data to a flat list
                emg_flat = [float(item) for item in emg]
                # recording.append(emg_flat.copy())
                print(emg_flat)
                recording.append(emg_flat.copy())

                if time.time() - timer > 5:
                    should_stop_recording = True

                now = time.time()
            else:
                time.sleep(0.001)

        # Terminate the recording
        q_terminate.put(True)

        # Generate a unique filename for the recording
        now = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        recording_filename = f"recording_{now}.csv"
        # Get the session folder path
        session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}', f'g_{self.gesture}')
        # Create the recording file
        recording_path = os.path.join(session_folder, recording_filename)
        os.makedirs(session_folder, exist_ok=True)
        np.savetxt(recording_path, np.array(recording, dtype=float), delimiter=",")

        # Update the recordings listbox
        self.load_recordings()

        # Display a confirmation message
        msgbox.showinfo("Recording Finished", f"Recording saved as {recording_filename}")

    def delete_recording_listbox(self, event):
        # Get selected item index
        selected_index = self.recordings_listbox.curselection()
        if selected_index:
            selected_filename = self.recordings_listbox.get(selected_index[0]) + '.csv'
            # Ask for confirmation
            if msgbox.askyesno("Delete recording for gesture", f"Are you sure you want to delete recording {selected_filename}?"):
                # Delete the csv file
                session_folder = os.path.join('user_data', f'u_{self.user_id}', f's_{self.session_id}', f'g_{self.gesture}')
                send2trash.send2trash(os.path.join(session_folder, selected_filename))
                # os.remove(os.path.join(session_folder, selected_filename))

                # Delete the selected item from listbox
                self.recordings_listbox.delete(selected_index[0])

                self.load_recordings()