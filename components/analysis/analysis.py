import os
import tkinter as tk

import plotly.express as px
import numpy as np
import pandas as pd
from scipy import signal
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from config import FONT
from constants import NUM_FEATURES_PER_SAMPLE, DATA_LEN, DATASET_SHIFT_SIZE, FEATURE_VECTOR_DIM


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

        # Features to include as options
        features = ["RMS", "MAV", "Variance", "Standard Deviation", "Peak Frequency", "EMG Raw"]

        # Frame for checkboxes
        checkbox_frame = tk.Frame(main_frame, bg=self.root.colour_config["bg"])
        checkbox_frame.pack(pady=10)

        for feature in features:
            self.feature_vars[feature] = tk.BooleanVar(value=False)  # Default all features disabled
            tk.Checkbutton(checkbox_frame, text=feature, var=self.feature_vars[feature],
                           bg=self.root.colour_config["bg"], fg=self.root.colour_config["fg"]).pack(anchor='w')

        # Add button for PCA analysis
        pca_button = tk.Button(main_frame, text="Run PCA", command=self.run_pca_analysis,
                               bg=self.root.colour_config["bg"],
                               fg=self.root.colour_config["fg"], relief=tk.RIDGE, borderwidth=1)

        pca_button.pack_configure(pady=10, ipady=5, fill=tk.X)

        # Pack the frame
        main_frame.pack(side='left', fill='both', expand=True)

    def run_pca_analysis(self):
        print("Running PCA analysis with features: ", [feature for feature, var in self.feature_vars.items() if var.get()])
        print("Loading files...")

        # Load all CSVs from the user_data folder
        if self.samples is None:
            self.samples, self.gesture_types = self.load_all_files()

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

        # Initialize PCA, you can specify `n_components` if you know how many you want to keep
        pca = PCA(n_components=2)  # For example, to reduce to 2 dimensions

        # Fit and transform the scaled data
        principal_components = pca.fit_transform(scaled_features)
        labels = {
            str(i): f"PC {i + 1} ({var:.1f}%)"
            for i, var in enumerate(pca.explained_variance_ratio_ * 100)
        }

        fig = px.scatter_matrix(
            principal_components,
            labels=labels,
            dimensions=range(2),
            color=self.gesture_types
        )
        # fig.update_traces(diagonal_visible=False)
        # fig.show()

        # In 3D
        pca = PCA(n_components=3)
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

            # Frequency-domain features
            if "Peak Frequency" in included_features:
                psd = []
                for channel_data in sample.T:
                    f, pxx = signal.welch(channel_data, fs=200, nperseg=100)
                    psd.append(pxx)
                peak_freqs = np.argmax(psd, axis=1)
                features_vector.append(peak_freqs)

            # Combine all features into a single feature vector for this sample
            features_vector = np.concatenate((features_vector), axis=None)
            extracted_features.append(features_vector)

        return np.array(extracted_features)

    def load_all_files(self):
        data = []
        gesture_types = []

        for root, dirs, files in os.walk("user_data"):
            for filename in files:
                if filename.endswith(".csv"):
                    data.append(pd.read_csv(os.path.join(root, filename), index_col=False))
                    if "/" in root:
                        gesture_types.append(root.split("/")[-1])
                    else:
                        gesture_types.append(root.split("\\")[-1])

        data_np = []
        for i in range(len(data)):
            data_np.append((gesture_types[i], data[i].to_numpy(dtype=np.float32)))

        # This will hold all our processed data points
        proc_samples = []
        gesture_types = []
        # For each csv, do our processing
        for i in tqdm(range(len(data_np))):
            gesture_type, rec = data_np[i]
            rec_samples = rec[:, :FEATURE_VECTOR_DIM]
            rec_length = rec.shape[0]
            for start in range(0, rec_length - DATA_LEN, DATASET_SHIFT_SIZE * 5):
                sample = rec_samples[start: start + DATA_LEN]
                # Append to list
                proc_samples.append(sample)
                gesture_types.append(gesture_type)

        data_np = np.array(proc_samples)
        print("Got " + str(len(data_np)) + " recordings and approximately " + str(len(data_np) * len(data_np[0])) + " samples.")
        return data_np, gesture_types

