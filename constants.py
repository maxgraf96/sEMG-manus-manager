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
