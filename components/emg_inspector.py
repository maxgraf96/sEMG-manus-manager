import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.transforms import BboxBase, Bbox

from constants import (
    DATA_CSV_HEADER_LIST,
    DATA_CSV_HEADER_STR,
    FEATURE_VECTOR_DIM,
    MODEL_OUTPUT_DIM,
    MYO_SR,
    DATASET_SHIFT_SIZE,
)


class EMGInspectorWindow(tk.Toplevel):
    def __init__(self, file_path, root):
        super().__init__()
        self.root = root
        self.title("EMG Inspector")
        self.geometry("1600x900")
        self.resizable(True, True)

        self.emg_inspector = EMGInspector(self.root, self, file_path)
        self.emg_inspector.pack(fill=tk.BOTH, expand=True)

    def load_file(self, file_path):
        self.emg_inspector.file_path = file_path

        # Reset the widgets
        for widget in self.emg_inspector.winfo_children():
            widget.destroy()

        self.emg_inspector.create_widgets()
        self.lift()


class EMGInspector(tk.Frame):
    def __init__(self, root, parent, file_path):
        super().__init__(root)
        self.root = root
        self.parent = parent
        self.file_path = file_path
        tk.Frame.__init__(self, parent)

        self.create_widgets()

    def create_widgets(self):
        if self.file_path is None:
            return

        # Set background to white
        self.config(bg=self.root.colour_config["bg"])

        # Add title label to the top of the window
        title_label = tk.Label(
            self,
            text="EMG Inspector",
            font=("Arial", 24),
            bg=self.root.colour_config["bg"],
        )
        title_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Add label for file name
        file_label = tk.Label(
            self,
            text=f"File: {self.file_path}",
            bg=self.root.colour_config["bg"],
            fg=self.root.colour_config["fg"],
        )
        file_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Read csv file
        self.data = np.genfromtxt(self.file_path, delimiter=",", skip_header=0)
        self.channels = self.data.shape[1]  # Assuming each column is a channel

        r_emg_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        r_emg_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        r_imu_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        r_imu_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        r_fingers_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        r_fingers_frame.pack(side=tk.TOP, padx=10, pady=5)
        r_hand_rotation_frame = tk.Frame(self, bg=self.root.colour_config["bg"])
        r_hand_rotation_frame.pack(side=tk.TOP, padx=10, pady=5)

        radio_label = tk.Label(
            r_emg_frame,
            text="Select Channel: ",
            bg=self.root.colour_config["bg"],
            fg=self.root.colour_config["fg"],
        )
        radio_label.pack(side=tk.LEFT)

        self.channel_var = tk.IntVar(value=0)  # Default to first channel
        for i in range(self.channels):
            target_frame = r_emg_frame
            if i > 8:
                target_frame = r_imu_frame
            if i > 18:
                target_frame = r_fingers_frame
            if i > 38:
                target_frame = r_hand_rotation_frame

            tk.Radiobutton(
                target_frame,
                text=f"{DATA_CSV_HEADER_LIST[i]}",
                variable=self.channel_var,
                value=i,
                bg=self.root.colour_config["bg"],
                command=self.update_plot,
            ).pack(side=tk.LEFT)

        # Matplotlib Figure and Canvas
        self.fig = Figure(figsize=(10, 6), dpi=100)  # Adjusted size for two plots
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(
            side=tk.TOP, fill=tk.BOTH, expand=False, anchor="center"
        )

        self.update_plot()

    def update_plot(self, event=None):
        channel_index = self.channel_var.get()
        sample = self.data[:, int(channel_index)].copy()

        self.fig.clear()

        # Raw data plot
        ax1 = self.fig.add_subplot(2, 2, 1)
        ax1.plot(sample)
        ax1.set_title(f"EMG Data - Channel {self.channel_var.get() + 1}")
        ax1.set_xlabel("Time (samples)")
        ax1.set_ylabel("Amplitude")

        # Spectrogram
        ax2 = self.fig.add_subplot(2, 2, 2)
        Pxx, freqs, bins, im = ax2.specgram(
            sample, NFFT=MYO_SR // 2, Fs=MYO_SR, noverlap=20, cmap="plasma"
        )
        ax2.set_title(f"Spectrogram - Channel {self.channel_var.get() + 1}")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Frequency (Hz)")
        self.fig.colorbar(im, ax=ax2, orientation="vertical", label="Intensity dB")

        # Peak frequency
        ax3 = self.fig.add_subplot(2, 2, 3)
        # For each timestep from the spectrogram, find the frequency with the highest intensity
        peak_freqs = np.argmax(Pxx, axis=0)
        ax3.plot(bins, freqs[peak_freqs])
        ax3.set_title(f"Peak Frequency - Channel {self.channel_var.get() + 1}")
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("Frequency (Hz)")
        ax3.set_ylim(0, 100)

        # RMS
        # thin linewidth
        ax4 = self.fig.add_subplot(2, 2, 4)
        # Get RMS for each window
        rms = []
        for i in range(0, len(sample), DATASET_SHIFT_SIZE):
            window = sample[i : i + MYO_SR]
            rms.append(np.sqrt(np.mean(window**2)))
        x = np.arange(0, len(sample), DATASET_SHIFT_SIZE) / MYO_SR
        ax4.plot(x, rms, linewidth=0.5)
        ax4.set_title(f"RMS - Channel {self.channel_var.get() + 1}")
        # ax4.set_xticks([])
        ax4.set_ylabel("Amplitude")

        self.fig.tight_layout(pad=3.0, w_pad=3.0, h_pad=3.0)

        self.canvas.draw()
