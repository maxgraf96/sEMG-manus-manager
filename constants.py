FEATURE_VECTOR_DIM = 8

# How many features and labels are contained in each CSV sample (columns)
NUM_FEATURES_PER_SAMPLE = 18
NUM_LABELS_PER_SAMPLE = 20

# For MANUS data, label indices out of all 20 collected values, expressed in indices AFTER separation from samples
MANUS_LABEL_INDICES = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

MODEL_OUTPUT_DIM = len(MANUS_LABEL_INDICES)

# Myo armband sample rate
MYO_SR = 200

DATA_LEN = MYO_SR * 2
# DATA_LEN = 10
DATASET_SHIFT_SIZE = 1


GESTURES = [
    # GENERAL
    'flexext_fist',
    'flexext_thumb',
    'flexext_index',
    'flexext_middle',
    'flexext_ring',
    'flexext_pinky',
    'finger_tap_surface',
    'thumbs_up',
    'point_index',
    'ab_add_all',
    'ab_add_thumb_index',
    'ab_add_index_middle',
    'ab_add_middle_ring',
    'ab_add_ring_pinky',
    # XRMI
    'tap_thumb',
    'tap_index',
    'tap_middle',
    'tap_ring',
    'tap_pinky',
    'pinched_tap_thumb_index',
    'pinched_tap_index_middle',
    'pinched_tap_middle_ring',
    'pinched_tap_ring_pinky',
    'melody'
]

XRMI_GESTURES = GESTURES[-10:-1]
