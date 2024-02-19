import os
from threading import Timer
import shutil
import csv
import tempfile

import numpy as np
import pandas as pd

from constants import FEATURE_VECTOR_DIM, MANUS_LABEL_INDICES

excluded_elements = ["delete_session_button", "theme_toggle_button"]


# Function to recursively iterate through all children of a widget
def configure_recursively(widget, config):
    bg_only_conf = {
        "bg": config["bg"]
    }

    try:
        if str(widget).split(".")[-1] in excluded_elements:
            pass
        else:
            widget.configure(config)
    except Exception as e:
        # Some items cannot have their foreground colour changed
        if "-fg" in e.__str__():
            widget.configure(bg_only_conf)
        else:
            pass
    for child in widget.winfo_children():
        try:
            if str(child.widget).split(".")[-1] in excluded_elements:
                continue
            child.configure(config)
        except Exception as e:
            # Some items cannot have their foreground colour changed
            if "-fg" in e.__str__():
                widget.configure(bg_only_conf)
            else:
                pass
        # Recursively apply the configuration to children's children
        configure_recursively(child, config)


def get_total_number_of_datapoints():
    # Get the total number of datapoints
    total_datapoints = 0
    for user_folder in os.listdir('user_data'):
        user_folder_path = os.path.join('user_data', user_folder)
        for session_folder in os.listdir(user_folder_path):
            session_folder_path = os.path.join(user_folder_path, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            for gesture_folder in os.listdir(session_folder_path):
                gesture_folder_path = os.path.join(session_folder_path, gesture_folder)
                if not os.path.isdir(gesture_folder_path):
                    continue
                for file in os.listdir(gesture_folder_path):
                    if file.endswith('.csv'):
                        file_path = os.path.join(gesture_folder_path, file)
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            total_datapoints += len(lines)
    return total_datapoints


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def create_visualiser_csv(data):
    """
    Create a CSV file from the data
    :param data: Numpy array in the shape of (1, sequence_length, MODEL_OUTPUT_DIM)
    :return: A path to a temporary csv file matching the following format: Frame,Hand_X,Hand_Y,Hand_Z,Thumb_CMC_X,Thumb_CMC_Y,Thumb_CMC_Z,Thumb_MCP_X,Thumb_MCP_Y,Thumb_MCP_Z,Thumb_DIP_X,Thumb_DIP_Y,Thumb_DIP_Z,Thumb_TIP_X,Thumb_TIP_Y,Thumb_TIP_Z,Index_CMC_X,Index_CMC_Y,Index_CMC_Z,Index_MCP_X,Index_MCP_Y,Index_MCP_Z,Index_PIP_X,Index_PIP_Y,Index_PIP_Z,Index_DIP_X,Index_DIP_Y,Index_DIP_Z,Index_TIP_X,Index_TIP_Y,Index_TIP_Z,Middle_CMC_X,Middle_CMC_Y,Middle_CMC_Z,Middle_MCP_X,Middle_MCP_Y,Middle_MCP_Z,Middle_PIP_X,Middle_PIP_Y,Middle_PIP_Z,Middle_DIP_X,Middle_DIP_Y,Middle_DIP_Z,Middle_TIP_X,Middle_TIP_Y,Middle_TIP_Z,Ring_CMC_X,Ring_CMC_Y,Ring_CMC_Z,Ring_MCP_X,Ring_MCP_Y,Ring_MCP_Z,Ring_PIP_X,Ring_PIP_Y,Ring_PIP_Z,Ring_DIP_X,Ring_DIP_Y,Ring_DIP_Z,Ring_TIP_X,Ring_TIP_Y,Ring_TIP_Z,Pinky_CMC_X,Pinky_CMC_Y,Pinky_CMC_Z,Pinky_MCP_X,Pinky_MCP_Y,Pinky_MCP_Z,Pinky_PIP_X,Pinky_PIP_Y,Pinky_PIP_Z,Pinky_DIP_X,Pinky_DIP_Y,Pinky_DIP_Z,Pinky_TIP_X,Pinky_TIP_Y,Pinky_TIP_Z
    """

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as temp_csv:
        writer = csv.writer(temp_csv)
        writer.writerow(
            ["Frame", "Hand_X", "Hand_Y", "Hand_Z", "Thumb_CMC_X", "Thumb_CMC_Y", "Thumb_CMC_Z", "Thumb_MCP_X",
             "Thumb_MCP_Y", "Thumb_MCP_Z", "Thumb_DIP_X", "Thumb_DIP_Y", "Thumb_DIP_Z", "Thumb_TIP_X", "Thumb_TIP_Y",
             "Thumb_TIP_Z", "Index_CMC_X", "Index_CMC_Y", "Index_CMC_Z", "Index_MCP_X", "Index_MCP_Y", "Index_MCP_Z",
             "Index_PIP_X", "Index_PIP_Y", "Index_PIP_Z", "Index_DIP_X", "Index_DIP_Y", "Index_DIP_Z", "Index_TIP_X",
             "Index_TIP_Y", "Index_TIP_Z", "Middle_CMC_X", "Middle_CMC_Y", "Middle_CMC_Z", "Middle_MCP_X",
             "Middle_MCP_Y", "Middle_MCP_Z", "Middle_PIP_X", "Middle_PIP_Y", "Middle_PIP_Z", "Middle_DIP_X",
             "Middle_DIP_Y", "Middle_DIP_Z", "Middle_TIP_X", "Middle_TIP_Y", "Middle_TIP_Z", "Ring_CMC_X",
             "Ring_CMC_Y", "Ring_CMC_Z", "Ring_MCP_X", "Ring_MCP_Y", "Ring_MCP_Z", "Ring_PIP_X", "Ring_PIP_Y",
             "Ring_PIP_Z", "Ring_DIP_X", "Ring_DIP_Y", "Ring_DIP_Z", "Ring_TIP_X", "Ring_TIP_Y", "Ring_TIP_Z",
             "Pinky_CMC_X", "Pinky_CMC_Y", "Pinky_CMC_Z", "Pinky_MCP_X", "Pinky_MCP_Y", "Pinky_MCP_Z", "Pinky_PIP_X",
             "Pinky_PIP_Y", "Pinky_PIP_Z", "Pinky_DIP_X", "Pinky_DIP_Y", "Pinky_DIP_Z", "Pinky_TIP_X", "Pinky_TIP_Y",
                "Pinky_TIP_Z"])
        for i in range(data.shape[1]):
            current_row = list(data[0][i])

            index_spread = current_row[0]
            index_mcp = current_row[1]
            index_pip = current_row[2]
            index_dip = current_row[3]
            middle_spread = current_row[4]
            middle_mcp = current_row[5]
            middle_pip = current_row[6]
            middle_dip = current_row[7]
            ring_spread = current_row[8]
            ring_mcp = current_row[9]
            ring_pip = current_row[10]
            ring_dip = current_row[11]
            pinky_spread = current_row[12]
            pinky_mcp = current_row[13]
            pinky_pip = current_row[14]
            pinky_dip = current_row[15]

            writer.writerow([
                # Frame, Hand_X, Hand_y, Hand_Z
                "0", "0", "0", "0",
                # Thumb_CMC_X, Thumb_CMC_Y, Thumb_CMC_Z
                "0", "0", "0",
                # Thumb_MCP_X, Thumb_MCP_Y, Thumb_MCP_Z
                "0", "0", "0",
                # Thumb_DIP_X, Thumb_DIP_Y, Thumb_DIP_Z
                "0", "0", "0",
                # Thumb_TIP_X, Thumb_TIP_Y, Thumb_TIP_Z
                "0", "0", "0",

                # Index_CMC_X, Index_CMC_Y, Index_CMC_Z
                "0", index_spread, "0",
                # Index_MCP_X, Index_MCP_Y, Index_MCP_Z
                index_mcp, "0", "0",
                # Index_PIP_X, Index_PIP_Y, Index_PIP_Z
                index_pip, "0", "0",
                # Index_DIP_X, Index_DIP_Y, Index_DIP_Z
                index_dip, "0", "0",
                # Index_TIP_X, Index_TIP_Y, Index_TIP_Z
                "0", "0", "0",

                # Middle_CMC_X, Middle_CMC_Y, Middle_CMC_Z
                "0", middle_spread, "0",
                # Middle_MCP_X, Middle_MCP_Y, Middle_MCP_Z
                middle_mcp, "0", "0",
                # Middle_PIP_X, Middle_PIP_Y, Middle_PIP_Z
                middle_pip, "0", "0",
                # Middle_DIP_X, Middle_DIP_Y, Middle_DIP_Z
                middle_dip, "0", "0",
                # Middle_TIP_X, Middle_TIP_Y, Middle_TIP_Z
                "0", "0", "0",

                # Ring_CMC_X, Ring_CMC_Y, Ring_CMC_Z
                "0", ring_spread, "0",
                # Ring_MCP_X, Ring_MCP_Y, Ring_MCP_Z
                ring_mcp, "0", "0",
                # Ring_PIP_X, Ring_PIP_Y, Ring_PIP_Z
                ring_pip, "0", "0",
                # Ring_DIP_X, Ring_DIP_Y, Ring_DIP_Z
                ring_dip, "0", "0",
                # Ring_TIP_X, Ring_TIP_Y, Ring_TIP_Z
                "0", "0", "0",

                # Pinky_CMC_X, Pinky_CMC_Y, Pinky_CMC_Z
                "0", pinky_spread, "0",
                # Pinky_MCP_X, Pinky_MCP_Y, Pinky_MCP_Z
                pinky_mcp, "0", "0",
                # Pinky_PIP_X, Pinky_PIP_Y, Pinky_PIP_Z
                pinky_pip, "0", "0",
                # Pinky_DIP_X, Pinky_DIP_Y, Pinky_DIP_Z
                pinky_dip, "0", "0",
                # Pinky_TIP_X, Pinky_TIP_Y, Pinky_TIP_Z
                "0", "0", "0"
            ])
        # Strip empty lines
        temp_csv.flush()
        os.fsync(temp_csv.fileno())

    print("Created temp CSV file at " + temp_csv.name + " with " + str(data.shape[1]) + " rows")

    return temp_csv.name


def update_visualiser_temp_file(temp_csv_path):
    # Delete all CSVs in the E:\Pycharm Projects 10\sEMG-manus-hand-renderer\resources\csvs folder
    for file in os.listdir("E:\\Pycharm Projects 10\\sEMG-manus-hand-renderer\\resources\\csvs"):
        if file.endswith(".csv"):
            os.remove(f"E:\\Pycharm Projects 10\\sEMG-manus-hand-renderer\\resources\\csvs\\{file}")

    # Copy the temp file to E:\Pycharm Projects 10\sEMG-manus-hand-renderer\resources\csvs
    shutil.copy(temp_csv_path, "E:\\Pycharm Projects 10\\sEMG-manus-hand-renderer\\resources\\csvs\\temp.csv")


def extract_hand_pose_data_from_gt_csv(filename):
    """
    Extract hand pose data from a ground truth CSV file - the ones containing EMG data and hand pose data
    :param filename: Path to the CSV file
    :return: Numpy array in the shape of (1, sequence_length, MODEL_OUTPUT_DIM)
    """

    data = pd.read_csv(filename, index_col=False)
    data = data.to_numpy(dtype=np.float32)
    data = np.expand_dims(data, axis=0)

    # Discard EMG columns
    data = data[:, :, FEATURE_VECTOR_DIM:]

    # Take only the indices we're interested in
    data = data[:, :, MANUS_LABEL_INDICES]

    return data