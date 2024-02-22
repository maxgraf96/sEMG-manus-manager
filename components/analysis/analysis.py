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

        for feature in features:
            self.feature_vars[feature] = tk.BooleanVar(value=False)  # Default all features disabled
            tk.Checkbutton(checkbox_frame, text=feature, var=self.feature_vars[feature],
                           bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]).pack(anchor='w')

        # Data len var
        data_len_analysis = tk.IntVar(value=DATA_LEN)
        data_len_label = tk.Label(main_frame, text=f"Data Length: {data_len_analysis} samples", font=(FONT, 12), bg=self.root.colour_config["bg"],
                                    fg=self.root.colour_config["fg"])
        data_len_label.pack_configure(pady=10, anchor='w')


        # Add button for PCA analysis
        pca_button = tk.Button(main_frame, text="Run PCA", command=self.run_pca_analysis,
                               bg=self.root.colour_config["bg"],
                               fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)

        pca_button.pack_configure(pady=10, ipady=5, anchor='w')
        # Make button 200px wide
        pca_button.config(width=20)

        # Pack the frame
        main_frame.pack_configure(side='left', fill='both', expand=False, anchor='nw', padx=20, pady=20)
        #Frame padding 20 px


    def run_pca_analysis(self):
        print("Running PCA analysis with features: ",
              [feature for feature, var in self.feature_vars.items() if var.get()])
        print("Loading files...")

        # Load all CSVs from the user_data folder
        if self.samples is None:
            self.samples, self.gesture_types, _ = load_all_files()

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
        pca = PCA(n_components=8)
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

    def extract_features(self):
        """
        Extracts time and frequency domain features from EMG samples.
        :return: numpy array of shape (n_samples, n_extracted_features)
        """
        extracted_features = []

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
                # Create an array for input data and an output array
                input_array = pyfftw.empty_aligned(400, dtype='complex128')
                output_array = pyfftw.empty_aligned(400, dtype='complex128')

                # Create an FFT object
                fft_object = pyfftw.FFTW(input_array, output_array)

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

        return np.array(extracted_features)


def load_all_files(dir="user_data"):
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
        for start in range(0, rec_length - DATA_LEN, DATASET_SHIFT_SIZE):
            sample = rec_samples[start: start + DATA_LEN]
            # Append to list
            proc_samples.append(sample)
            gesture_types.append(gesture_type)

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