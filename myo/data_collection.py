import multiprocessing
import time

import numpy as np

from myo.worker_myo import worker_myo
from manus.worker_manus import worker_manus


def worker_collection(q_myo, q_manus, q_result, q_terminate, q_myo_ready):
    p_myo = multiprocessing.Process(target=worker_myo, args=(q_myo, q_terminate, q_myo_ready,))
    p_manus = multiprocessing.Process(target=worker_manus, args=(q_manus, q_terminate,))
    p_myo.start()
    p_manus.start()

    # emgs is a list of lists acting like a queue
    timer = time.time()
    avg_fps = 0
    counter = 0

    try:
        # while session_detail.is_recording:
        while q_terminate.empty():
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Avg fps: ", counter / (time.time() - timer))
        print("Finished recording")
        # Close the socket and context
        # socket.close()
        # context.term()

    # Finished
    p_myo.join(100)
    p_manus.join(100)
    finished = True


def start_recording(q_myo, q_manus, q_result, q_terminate, q_myo_ready):
    # Clear all queues
    q_myo.empty()
    q_manus.empty()
    q_result.empty()

    # Start a new recording
    p_collection = multiprocessing.Process(target=worker_collection, args=(q_myo, q_manus, q_result, q_terminate, q_myo_ready,))
    p_collection.start()
