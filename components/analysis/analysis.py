import os
import tkinter as tk

import plotly.express as px
import numpy as np
import pandas as pd
from pyfftw import pyfftw
from scipy import signal
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import tkinter.messagebox as msgbox
from tkinter import ttk

from config import FONT
from constants import NUM_FEATURES_PER_SAMPLE, DATA_LEN, DATASET_SHIFT_SIZE, FEATURE_VECTOR_DIM, MYO_SR


class AnalysisFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent, bg=root.colour_config["bg"])
        self.root = root

        # Data
        self.samples = None
        self.gesture_types = None

        # Dictionary to store the variables associated with each feature's checkbox
        self.feature_vars = {}

        # Vars for user selections
        self.selected_users = []
        self.selected_sessions = []
        self.selected_gestures = []

        # Keep track of available data structure
        self.all_users = []
        self.all_sessions = []
        self.all_speeds = []

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Analysis", font=(FONT, 20),
                 bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        # ---------------
        # MAIN CONTENT FRAME
        # ---------------
        main_frame = tk.Frame(self, name="main_content", bg=self.root.colour_config["bg"])
        main_frame.pack_configure(side='left', fill='both', expand=False, anchor='nw', padx=20, pady=20)

        # ---------------
        # PCA label
        # ---------------
        pca_label = tk.Label(main_frame, text="Principal Component Analysis", font=(FONT, 16),
                             bg=self.root.colour_config["bg"],
                             fg=self.root.colour_config["fg"])
        pca_label.pack_configure(pady=10, anchor='w')

        # ---------------
        # MULTIPLE CHOICE BOXES FOR USER / SESSIONS / SPEED
        # ---------------
        # Subframe for data filtering
        data_filter_frame = tk.Frame(main_frame, bg=self.root.colour_config["bg"])
        data_filter_frame.pack_configure(fill=tk.BOTH, expand=False, pady=10)

        # Listbox for Users
        tk.Label(data_filter_frame, text="Users", font=(FONT, 12),
                 bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
        ).grid(row=1, column=0, sticky='w', padx=10)
        self.user_listbox = tk.Listbox(data_filter_frame, selectmode=tk.MULTIPLE, height=6,
                                       bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"], exportselection=False)
        self.user_listbox.grid(row=2, column=0, padx=10, pady=5, sticky='ns')

        # Listbox for Sessions
        tk.Label(data_filter_frame, text="Sessions", font=(FONT, 12),
                 bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
        ).grid(row=1, column=1, sticky='w', padx=10)
        self.session_listbox = tk.Listbox(data_filter_frame, selectmode=tk.MULTIPLE, height=6,
                                          bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"], exportselection=False)
        self.session_listbox.grid(row=2, column=1, padx=10, pady=5, sticky='ns')

        # Listbox for Gestures
        tk.Label(data_filter_frame, text="Gestures", font=(FONT, 12),
                 bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
        ).grid(row=1, column=2, sticky='w', padx=10)
        self.gesture_listbox = tk.Listbox(data_filter_frame, selectmode=tk.MULTIPLE, height=6,
                                          bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"], exportselection=False)
        self.gesture_listbox.grid(row=2, column=2, padx=10, pady=5, sticky='ns')

        # Listbox for Speeds
        tk.Label(data_filter_frame, text="Speeds", font=(FONT, 12),
                    bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
                ).grid(row=1, column=3, sticky='w', padx=10)
        self.speed_listbox = tk.Listbox(data_filter_frame, selectmode=tk.MULTIPLE, height=6,
                                        bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"], exportselection=False)
        self.speed_listbox.grid(row=2, column=3, padx=10, pady=5, sticky='ns')

        # ---------------
        # FEATURES CHECKBOXES
        # ---------------
        included_features_label = tk.Label(main_frame, text="Included Features", font=(FONT, 12),
                                           bg=self.root.colour_config["bg"],
                                           fg=self.root.colour_config["fg"])
        included_features_label.pack_configure(pady=10, anchor='w')

        # Features to include as options
        features = ["RMS", "MAV", "Variance", "Standard Deviation", "Peak Frequency", "EMG Raw", "IASD", "IEAV"]

        # Frame for checkboxes
        checkbox_frame = tk.Frame(main_frame, bg=self.root.colour_config["bg"])
        checkbox_frame.pack_configure(pady=10, anchor='w')

        for i, feature in enumerate(features):
            var = tk.IntVar(value=0)
            self.feature_vars[feature] = var
            checkbox = tk.Checkbutton(
                checkbox_frame, text=feature, variable=var,
                bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
            )
            checkbox.grid(row=i // 2, column=i % 2, sticky='w')

        # ---------------
        # DATA LENGTH SLIDER
        # ---------------
        self.data_len_analysis = tk.IntVar(value=DATA_LEN)
        data_len_label = tk.Label(
            main_frame, text=f"Data Length: {self.data_len_analysis.get()} samples", font=(FONT, 12),
            bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
        )
        data_len_label.pack_configure(pady=10, anchor='w')
        self.last_data_len = DATA_LEN

        def dl_slider_update(e):
            value = self.data_len_analysis.get()
            if value < 100:
                # Round to nearest 10
                value = int(round(value / 10.0)) * 10
            else:
                # Round to nearest 100
                value = int(round(value / 100.0)) * 100
            self.data_len_analysis.set(value)
            data_len_label.config(text=f"Data Length: {self.data_len_analysis.get()} samples")

        data_len_slider = tk.Scale(
            main_frame, from_=1, to=1000, orient='horizontal',
            variable=self.data_len_analysis,
            bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"],
            command=lambda e: dl_slider_update(e)
        )
        data_len_slider.pack_configure(pady=10, anchor='w')
        data_len_slider.config(length=200)

        # ---------------
        # PCA COMPONENTS SLIDER
        # ---------------
        self.n_components_pca = tk.IntVar(value=3)
        n_components_label = tk.Label(
            main_frame, text=f"Number of Principal Components: {self.n_components_pca.get()}",
            font=(FONT, 12),
            bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]
        )
        n_components_label.pack_configure(pady=10, anchor='w')

        n_components_slider = tk.Scale(
            main_frame, from_=1, to=20, orient='horizontal', variable=self.n_components_pca,
            bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"],
            command=lambda e: n_components_label.config(
                text=f"Number of Principal Components: {self.n_components_pca.get()}"
            )
        )
        n_components_slider.pack_configure(pady=10, anchor='w')
        n_components_slider.config(length=200)

        # ---------------
        # BUTTON & PROGRESS BAR
        # ---------------
        buttongrid = tk.Frame(main_frame, bg=self.root.colour_config["bg"])
        buttongrid.pack_configure(pady=10, anchor='w')

        # Add button for PCA analysis
        pca_button = tk.Button(
            buttongrid, text="Run PCA", command=self.run_pca_analysis,
            bg=self.root.colour_config["bg"],
            fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1, width=20
        )
        pca_button.grid(row=0, column=0, sticky='w')

        # Progressbar
        self.progressbar = ttk.Progressbar(buttongrid, orient='horizontal', length=200, mode='determinate')
        self.progressbar.grid(row=0, column=1, sticky='w', padx=24)
        # Hide progressbar by default
        self.progressbar.grid_forget()

        self.populate_data_selections()

    # ------------------------------------------------------------------
    # Function to parse the directory structure and populate the 3 listboxes
    # ------------------------------------------------------------------
    def populate_data_selections(self):
        base_dir = "user_data"
        # Parse for all users, sessions, speeds
        users, sessions, gestures = parse_user_data_structure(base_dir)

        self.all_users = sorted(list(users))
        self.all_sessions = sorted(list(sessions))
        self.all_gestures = sorted(list(gestures))
        self.all_speeds = ["slow", "medium", "fast"]

        # Clear old entries
        self.user_listbox.delete(0, tk.END)
        self.session_listbox.delete(0, tk.END)
        self.gesture_listbox.delete(0, tk.END)
        self.speed_listbox.delete(0, tk.END)

        # Populate
        for u in self.all_users:
            self.user_listbox.insert(tk.END, u)
        for s in self.all_sessions:
            self.session_listbox.insert(tk.END, s)
        for gest in self.all_gestures:
            self.gesture_listbox.insert(tk.END, gest)
        for speed in self.all_speeds:
            self.speed_listbox.insert(tk.END, speed)

    # ------------------------------------------------------------------
    # Actually run the PCA analysis
    # ------------------------------------------------------------------
    def run_pca_analysis(self):
        # Check that at least one feature is selected
        if not any(var.get() for var in self.feature_vars.values()):
            msgbox.showinfo("Ehm", "Please select at least one feature to include in the analysis.")
            return

        # Grab selected items from the listboxes
        self.selected_users = [self.all_users[i] for i in self.user_listbox.curselection()]
        self.selected_sessions = [self.all_sessions[i] for i in self.session_listbox.curselection()]
        self.selected_gestures = [self.all_gestures[i] for i in self.gesture_listbox.curselection()]
        self.selected_speeds = [self.all_speeds[i] for i in self.speed_listbox.curselection()]

        # If the user hasn't selected anything, we might want to treat that as "select all"
        if len(self.selected_users) == 0:
            self.selected_users = self.all_users
        if len(self.selected_sessions) == 0:
            self.selected_sessions = self.all_sessions
        if len(self.selected_gestures) == 0:
            self.selected_gestures = self.all_gestures
        if len(self.selected_speeds) == 0:
            self.selected_speeds = self.all_speeds


        # Show progressbar
        self.progressbar.grid(row=0, column=1, sticky='w', padx=24)
        self.progressbar["value"] = 0

        print("\n\nRunning PCA analysis with features: ",
              [feature for feature, var in self.feature_vars.items() if var.get()])
        print("Selected users:", self.selected_users)
        print("Selected sessions:", self.selected_sessions)
        print("Selected gestures:", self.selected_gestures)
        print("Selected speeds:", self.selected_speeds)
        print("Loading files...")

        # Load all CSVs from the user_data folder
        if self.samples is None or self.data_len_analysis.get() != self.last_data_len:
            self.samples, self.gesture_types, _ = load_all_files(
                data_len=self.data_len_analysis.get(),
                progressbar=self.progressbar,
                selected_users=self.selected_users,
                selected_sessions=self.selected_sessions,
                selected_gestures=self.selected_gestures,
                selected_speeds=self.selected_speeds
            )

            # Get minimum length of all samples
            if len(self.samples) == 0:
                msgbox.showinfo("No Data", "No samples found with the selected filters!")
                self.progressbar.grid_forget()
                return

            min_length = min([sample.shape[0] for sample in self.samples])
            # Cut all to min_length so they are homogenous
            self.samples = [sample[:min_length, :FEATURE_VECTOR_DIM] for sample in self.samples]

        print("Extracting features...")
        # Extract features
        features = self.extract_features()

        print("Features shape:", features.shape)
        print("Running PCA...")

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        # PCA
        pca = PCA(n_components=self.n_components_pca.get())
        principal_components = pca.fit_transform(scaled_features)
        total_var = sum(pca.explained_variance_ratio_) * 100
        fig = px.scatter_3d(
            principal_components, x=0, y=1, z=2,
            color=self.gesture_types,
            title=f'Total Explained Variance: {total_var:.2f}%',
            labels={
                str(i): f"PC {i + 1} ({var:.1f}%)"
                for i, var in enumerate(pca.explained_variance_ratio_ * 100)
            }
        )
        fig.show()

        print("Explained variance ratio:", pca.explained_variance_ratio_)
        print("Total explained variance ratio:", sum(pca.explained_variance_ratio_))

        # Update last data len
        self.last_data_len = self.data_len_analysis.get()

        # Hide progressbar
        self.progressbar.grid_forget()

    # ------------------------------------------------------------------
    # Extract selected features
    # ------------------------------------------------------------------
    def extract_features(self):
        """
        Extracts time and frequency domain features from EMG samples.
        :return: numpy array of shape (n_samples, n_extracted_features)
        """
        extracted_features = []

        # Peak frequency setup
        sample_length = self.samples[0].shape[0]
        # Create an array for input data and an output array
        input_array = pyfftw.empty_aligned(sample_length, dtype='complex128')
        output_array = pyfftw.empty_aligned(sample_length, dtype='complex128')
        # Create an FFT object
        fft_object = pyfftw.FFTW(input_array, output_array)

        self.progressbar["value"] = 0
        self.progressbar.step(0)
        counter = 0

        for sample in tqdm(self.samples):
            included_features = [feature for feature, var in self.feature_vars.items() if var.get()]
            features_vector = []

            # "EMG Raw"
            if "EMG Raw" in included_features:
                features_vector.append(sample)

            # Time-domain
            if "MAV" in included_features:
                mav = np.mean(np.abs(sample), axis=0)
                features_vector.append(mav)

            if "RMS" in included_features:
                rms = np.sqrt(np.mean(np.square(sample), axis=0))
                features_vector.append(rms)

            if "Variance" in included_features:
                var = np.var(sample, axis=0)
                features_vector.append(var)

            if "Standard Deviation" in included_features:
                std = np.std(sample, axis=0)
                features_vector.append(std)

            if "IASD" in included_features:
                # Compute Integrated Absolute of second derivative
                for channel_data in sample.T:
                    iasd = integrated_absolute_second_derivative(channel_data)
                    features_vector.append(iasd)

            if "IEAV" in included_features:
                # Compute Integrated Exponential of Absolute Value
                for channel_data in sample.T:
                    ieav = integrated_exponential_of_absolute_value(channel_data)
                    features_vector.append(ieav)

            # Frequency-domain
            if "Peak Frequency" in included_features:
                psd = []
                for channel_data in sample.T:
                    # Fill the input array with your signal
                    input_array[:] = channel_data + 0j  # Ensure the signal is complex
                    # Execute the FFT
                    fft_object()
                    magnitude_spectrum = np.abs(output_array)
                    # Example: store median freq or peak freq from the magnitude spectrum
                    median_freq = np.median(magnitude_spectrum)
                    psd.append(median_freq)
                features_vector.append(psd)

            # Combine all features into a single feature vector for this sample
            features_vector = np.concatenate(features_vector, axis=None)
            extracted_features.append(features_vector)

            counter += 1
            if counter % 1000 == 0:
                self.progressbar["value"] = 100 * (counter / len(self.samples))
                self.progressbar.update()

        return np.array(extracted_features)


# ------------------------------------------------------------------
# Updated load_all_files with user/session/speed filters
# ------------------------------------------------------------------
def load_all_files(dir="user_data", data_len=DATA_LEN, progressbar=None,
                   selected_users=None, selected_sessions=None, selected_gestures=None, selected_speeds=None):
    data_recordings = []
    gesture_types = []

    # If no filters are provided, treat them as empty lists
    if selected_users is None:
        selected_users = []
    if selected_sessions is None:
        selected_sessions = []
    if selected_gestures is None:
        selected_gestures = []
    if selected_speeds is None:
        selected_speeds = []

    # Walk user_data directory
    for root, dirs, files in os.walk(dir):
        for filename in files:
            if filename.endswith(".csv"):
                # We make a decision about whether this file belongs to a user, session, speed
                # Example assumption:
                # Path might look like: user_data/<user>/<session>/<speed>/<gestureType>/some_file.csv
                # Adjust your logic to match your actual directory structure
                path_parts = root.split(os.sep)

                # Very naive approach: we guess indexes for user, session, speed
                # E.g. path_parts = ['user_data', 'userA', 'session_01', 'fast', 'grasp']
                # Just be sure your structure is consistent
                user_part = path_parts[1] if len(path_parts) > 1 else None
                session_part = path_parts[2] if len(path_parts) > 2 else None
                gesture_part = path_parts[3] if len(path_parts) > 3 else None
                speed = filename.split("_")[1]

                # Filter check
                if user_part not in selected_users:
                    continue
                if session_part not in selected_sessions:
                    continue
                if gesture_part not in selected_gestures:
                    continue
                if speed not in selected_speeds:
                    continue

                full_csv_path = os.path.join(root, filename)
                df = pd.read_csv(full_csv_path, index_col=False)
                data_recordings.append(df)

                # The last folder might be the gesture label
                gesture_label = path_parts[-1]  # e.g. 'grasp'
                gesture_types.append(gesture_label)

    # Convert them to arrays
    recordings_np = []
    for i in range(len(data_recordings)):
        recordings_np.append((gesture_types[i], data_recordings[i].to_numpy(dtype=np.float32)))

    # This will hold all our processed data points
    proc_samples = []
    final_gesture_types = []

    # For each CSV, do our processing
    for i in tqdm(range(len(recordings_np))):
        gesture_type, rec = recordings_np[i]
        rec_samples = rec[:, :FEATURE_VECTOR_DIM]
        rec_length = rec.shape[0]
        for start in range(0, rec_length - data_len, DATASET_SHIFT_SIZE):
            sample = rec_samples[start: start + data_len]
            proc_samples.append(sample)
            final_gesture_types.append(gesture_type)

        if progressbar is not None:
            progressbar["value"] = (i + 1) / len(recordings_np) * 100
            progressbar.update()

    all_in_one = np.array(proc_samples)
    print(f"Loaded {len(data_recordings)} recordings matching the filters.")
    print(f"Got approximately {len(all_in_one)} samples.")
    return all_in_one, final_gesture_types, recordings_np


def parse_user_data_structure(base_dir="user_data"):
    """
    Example helper function to parse the user_data folder to list all possible
    users, sessions, speeds. Adjust logic to your real directory structure.
    Returns sets: (users, sessions, speeds).
    """
    users = set()
    sessions = set()
    gestures = set()

    for root, dirs, files in os.walk(base_dir):
        # We assume path: user_data/<user>/<session>/<speed>/<gestureType>
        path_parts = root.split(os.sep)
        if len(path_parts) > 1:
            users.add(path_parts[1])
        if len(path_parts) > 2:
            sessions.add(path_parts[2])
        if len(path_parts) > 3:
            gestures.add(path_parts[3])

    return users, sessions, gestures


def integrated_absolute_second_derivative(x):
    # Compute the first derivative
    first_derivative = np.diff(x)
    # Compute the second derivative
    second_derivative = np.diff(first_derivative)
    # Compute the Integrated Absolute of the Second Derivative (IASD)
    iasd = np.sum(np.abs(second_derivative))
    return iasd

def integrated_exponential_of_absolute_value(x):
    # Compute the absolute value
    absolute = np.abs(x) * 0.001
    # Compute the exponential
    exponential = np.exp(absolute)
    # Compute the integral of the exponential
    integral = np.sum(exponential)
    return integral
