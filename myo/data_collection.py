import multiprocessing
import time

import numpy as np

from myo.worker_myo import worker_myo
from manus.worker_manus import worker_manus

# import zmq

# Myo setup
q_myo = multiprocessing.Queue()

# MANUS setup
q_manus = multiprocessing.Queue()


def worker_collection(q_myo, q_manus, q_result, q_terminate, q_myo_ready):
    p_myo = multiprocessing.Process(target=worker_myo, args=(q_myo, q_terminate, q_myo_ready,))
    # p_manus = multiprocessing.Process(target=worker_manus, args=(q_manus,))
    p_myo.start()
    # p_manus.start()

    # emgs is a list of lists acting like a queue
    recording = []
    timer = time.time()
    avg_fps = 0
    counter = 0
    try:
        # while session_detail.is_recording:
        while q_terminate.empty():
            while not (q_myo.empty()):
                if q_myo.qsize() == 0:
                    continue
                counter += 1
                emg = list(q_myo.get())

                # Convert the data to a flat list
                emg_flat = [float(item) for item in emg]
                q_result.put(emg_flat.copy())
                # recording.append(emg_flat.copy())

                # Pack the floats as binary data
                # packed_data = struct.pack('{}f'.format(len(flat_data)), *flat_data)
                # Send via zmq
                # socket.send(packed_data)
                # Receive the response from the server
                # response = socket.recv()

                # if time.time() - timer > 5:
                #     raise KeyboardInterrupt

                now = time.time()

    except KeyboardInterrupt:
        print("Avg fps: ", counter / (time.time() - timer))
        print("Finished recording")
        # Close the socket and context
        # socket.close()
        # context.term()

    # Finished
    p_myo.join(100)
    # p_manus.terminate()
    finished = True


def start_recording(q_result, q_terminate, q_myo_ready):
    # Clear all queues
    q_myo.empty()
    q_manus.empty()
    q_result.empty()

    # Start a new recording
    p_collection = multiprocessing.Process(target=worker_collection, args=(q_myo, q_manus, q_result, q_terminate, q_myo_ready,))
    p_collection.start()