FEATURE_VECTOR_DIM = 8

# How many features and labels are contained in each CSV sample (columns)
NUM_FEATURES_PER_SAMPLE = 18
NUM_LABELS_PER_SAMPLE = 20

# For MANUS data, label indices out of all 20 collected values, expressed in indices AFTER separation from samples
MANUS_LABEL_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

MODEL_OUTPUT_DIM = len(MANUS_LABEL_INDICES)

# Myo armband sample rate
MYO_SR = 200

DATA_LEN = MYO_SR * 2
# DATA_LEN = 10
DATASET_SHIFT_SIZE = 1


GESTURES = [
    # GENERAL
    "flexext_fist",
    "flexext_thumb",
    "flexext_index",
    "flexext_middle",
    "flexext_ring",
    "flexext_pinky",
    "finger_tap_surface",
    "thumbs_up",
    "point_index",
    "ab_add_all",
    "ab_add_thumb_index",
    "ab_add_index_middle",
    "ab_add_middle_ring",
    "ab_add_ring_pinky",
    # XRMI
    "tap_thumb",
    "tap_index",
    "tap_middle",
    "tap_ring",
    "tap_pinky",
    "pinched_tap_thumb_index",
    "pinched_tap_index_middle",
    "pinched_tap_middle_ring",
    "pinched_tap_ring_pinky",
    "melody",
]

XRMI_GESTURES = GESTURES[-10:-1]

header_emg = ",".join([f"emg_{i}" for i in range(8)])
header_imu = [
    "imu_quat_w",
    "imu_quat_x",
    "imu_quat_y",
    "imu_quat_z",
    "imu_acc_x",
    "imu_acc_y",
    "imu_acc_z",
    "imu_gyro_x",
    "imu_gyro_y",
    "imu_gyro_z",
]
header_fingers = [
    "thumb_spread",
    "thumb_mcp",
    "thumb_pip",
    "thumb_dip",
    "index_spread",
    "index_mcp",
    "index_pip",
    "index_dip",
    "middle_spread",
    "middle_mcp",
    "middle_pip",
    "middle_dip",
    "ring_spread",
    "ring_mcp",
    "ring_pip",
    "ring_dip",
    "pinky_spread",
    "pinky_mcp",
    "pinky_pip",
    "pinky_dip",
]
header_hand_rotation = ["wrist_quat_x", "wrist_quat_y", "wrist_quat_z", "wrist_quat_w"]
DATA_CSV_HEADER_STR = (
    header_emg
    + ","
    + ",".join(header_imu)
    + ","
    + ",".join(header_fingers)
    + ","
    + ",".join(header_hand_rotation)
)
DATA_CSV_HEADER_LIST = DATA_CSV_HEADER_STR.split(",")
