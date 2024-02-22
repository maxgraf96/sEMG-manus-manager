import os
import tkinter as tk

import plotly.express as px
import numpy as np
import pandas as pd
from matplotlib import mlab
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

        self.samples = None
        self.gesture_types = None

        # Dictionary to store the variables associated with each feature's checkbox
        self.feature_vars = {}

        self.create_widgets()
        self.pack_configure(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        top_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Analysis", font=(FONT, 20), bg=self.root.colour_config["bg"],
                 fg=self.root.colour_config["fg"]).pack()

        # Create frame for the main content
        main_frame = tk.Frame(self, name="testoo", bg=self.root.colour_config["bg"])

        pca_label = tk.Label(main_frame, text="Principal Component Analysis", font=(FONT, 16), bg=self.root.colour_config["bg"],
                                fg=self.root.colour_config["fg"])
        pca_label.pack_configure(pady=10, anchor='w')
        included_features_label = tk.Label(main_frame, text="Included Features", font=(FONT, 12), bg=self.root.colour_config["bg"],
                                             fg=self.root.colour_config["fg"])
        included_features_label.pack_configure(pady=10, anchor='w')

        # Features to include as options
        features = ["RMS", "MAV", "Variance", "Standard Deviation", "Peak Frequency", "EMG Raw", "IASD", "IEAV"]

        # Frame for checkboxes
        checkbox_frame = tk.Frame(main_frame, bg=self.root.colour_config["bg"])
        checkbox_frame.pack_configure(pady=10, anchor='w')

        # Create a checkbox for each feature, use 2 columns
        for i, feature in enumerate(features):
            var = tk.IntVar(value=0)
            self.feature_vars[feature] = var
            checkbox = tk.Checkbutton(checkbox_frame, text=feature, variable=var, bg=self.root.colour_config["bg"],
                                      fg=self.root.colour_config["fg"])
            checkbox.grid(row=i // 2, column=i % 2, sticky='w')

        # Data len var
        self.data_len_analysis = tk.IntVar(value=DATA_LEN)
        data_len_label = tk.Label(main_frame, text=f"Data Length: {self.data_len_analysis.get()} samples", font=(FONT, 12), bg=self.root.colour_config["bg"],
                                    fg=self.root.colour_config["fg"])
        data_len_label.pack_configure(pady=10, anchor='w')
        self.last_data_len = DATA_LEN
        # Data len slider
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

        data_len_slider = tk.Scale(main_frame, from_=1, to=1000, orient='horizontal', variable=self.data_len_analysis,
                                      bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"], command=lambda e: dl_slider_update(e))
        data_len_slider.pack_configure(pady=10, anchor='w')
        data_len_slider.config(length=200)

        # Num components slider
        self.n_components_pca = tk.IntVar(value=3)
        n_components_label = tk.Label(main_frame, text=f"Number of Principal Components: {self.n_components_pca.get()}", font=(FONT, 12), bg=self.root.colour_config["bg"],
                                    fg=self.root.colour_config["fg"])
        n_components_label.pack_configure(pady=10, anchor='w')
        # Num components slider
        n_components_slider = tk.Scale(main_frame, from_=1, to=20, orient='horizontal', variable=self.n_components_pca,
                                        bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"], command=lambda e: n_components_label.config(text=f"Number of Principal Components: {self.n_components_pca.get()}"))
        n_components_slider.pack_configure(pady=10, anchor='w')
        n_components_slider.config(length=200)

        # Make grid with button and progressbar
        buttongrid = tk.Frame(main_frame, bg=self.root.colour_config["bg"])
        buttongrid.pack_configure(pady=10, anchor='w')

        # Add button for PCA analysis
        pca_button = tk.Button(buttongrid, text="Run PCA", command=self.run_pca_analysis,
                               bg=self.root.colour_config["bg"],
                               fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1, width=20)

        # Progressbar
        self.progressbar = tk.ttk.Progressbar(buttongrid, orient='horizontal', length=200, mode='determinate')

        pca_button.grid(row=0, column=0, sticky='w')
        self.progressbar.grid(row=0, column=1, sticky='w', padx=24)
        # Hide progressbar
        self.progressbar.grid_forget()


        # Pack the frame
        main_frame.pack_configure(side='left', fill='both', expand=False, anchor='nw', padx=20, pady=20)
        #Frame padding 20 px


    def run_pca_analysis(self):
        if not any(var.get() for var in self.feature_vars.values()):
            # Show error message
            msgbox.showinfo("Ehm", "Please select at least one feature to include in the analysis.")
            return

        # Show progressbar
        self.progressbar.grid(row=0, column=1, sticky='w', padx=24)

        print("")
        print("")
        print("Running PCA analysis with features: ",
              [feature for feature, var in self.feature_vars.items() if var.get()])
        print("Loading files...")

        # Load all CSVs from the user_data folder
        if self.samples is None or self.data_len_analysis.get() != self.last_data_len:
            self.samples, self.gesture_types, _ = load_all_files(data_len=self.data_len_analysis.get(), progressbar=self.progressbar)

            # Get minimum length of all samples
            min_length = min([sample.shape[0] for sample in self.samples])
            # Cut all to min_length so they are homogenous and discard everything but emg data from samples for now
            self.samples = [sample[:min_length, :FEATURE_VECTOR_DIM] for sample in self.samples]

        print("Extracting features...")
        # Extract features
        features = self.extract_features()

        print("Features shape: " + str(features.shape))
        print("Running PCA...")

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        # In 3D
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

    def extract_features(self):
        """
        Extracts time and frequency domain features from EMG samples.
        :return: numpy array of shape (n_samples, n_extracted_features)
        """
        extracted_features = []

        # Peak frequency stuff
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
            # Check which features are included in the var
            included_features = [feature for feature, var in self.feature_vars.items() if var.get()]

            features_vector = []

            # Just orig data
            if "EMG Raw" in included_features:
                features_vector.append(sample)

            # Time-domain features
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

            # Frequency-domain features
            if "Peak Frequency" in included_features:
                psd = []

                for channel_data in sample.T:
                    # Fill the input array with your signal
                    input_array[:] = channel_data + 0j  # Ensure the signal is complex

                    # Execute the FFT
                    fft_object()

                    magnitude_spectrum = np.abs(output_array)

                    # Get median frequency
                    median_freq = np.median(magnitude_spectrum)

                    psd.append(median_freq)

                # peak_freqs = np.argmax(psd, axis=1)
                features_vector.append(psd)

            # Combine all features into a single feature vector for this sample
            features_vector = np.concatenate((features_vector), axis=None)
            extracted_features.append(features_vector)

            counter += 1
            if counter % 1000 == 0:
                self.progressbar["value"] = 100 * (counter / len(self.samples))
                self.progressbar.update()

        return np.array(extracted_features)


def load_all_files(dir="user_data", data_len=DATA_LEN, progressbar=None):
    data_recordings = []
    gesture_types = []

    for root, dirs, files in os.walk(dir):
        for filename in files:
            if filename.endswith(".csv"):
                data_recordings.append(pd.read_csv(os.path.join(root, filename), index_col=False))
                if "/" in root:
                    gesture_types.append(root.split("/")[-1])
                else:
                    gesture_types.append(root.split("\\")[-1])

    recordings_np = []
    for i in range(len(data_recordings)):
        recordings_np.append((gesture_types[i], data_recordings[i].to_numpy(dtype=np.float32)))

    # This will hold all our processed data points
    proc_samples = []
    gesture_types = []
    # For each csv, do our processing
    for i in tqdm(range(len(recordings_np))):
        gesture_type, rec = recordings_np[i]
        rec_samples = rec[:, :FEATURE_VECTOR_DIM]
        rec_length = rec.shape[0]
        for start in range(0, rec_length - data_len, DATASET_SHIFT_SIZE):
            sample = rec_samples[start: start + data_len]
            # Append to list
            proc_samples.append(sample)
            gesture_types.append(gesture_type)

        if progressbar is not None:
            progressbar["value"] = (i + 1) / len(recordings_np) * 100
            progressbar.update()

    all_in_one = np.array(proc_samples)
    print(f"Got {len(data_recordings)} recordings and approximately {len(all_in_one)} samples.")
    return all_in_one, gesture_types, recordings_np


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