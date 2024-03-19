import struct

import zmq


def worker_manus(q, q_terminate):
    # Prepare our context and socket
    context = zmq.Context()
    socket = context.socket(zmq.PULL)

    # Connect to the server socket
    socket.connect("tcp://127.0.0.1:5555")

    # Worker function
    while q_terminate.empty():
        # Receive raw bytes from MANUS
        message = socket.recv()

        # Parse: The first 20 floats in a message are the finger data
        finger_data = struct.unpack("20f", message[0:80])

        # The next 4 floats are the quaternion describing the wrist orientation
        wrist_quat = struct.unpack("4f", message[80:96])

        # At position 20 we have the timestamp - q is a long long (8 bytes)
        timestamp = struct.unpack("q", message[96:104])

        data = list(finger_data)
        data += list(wrist_quat)
        data.append(timestamp[0])

        # Add to the queue
        q.put(data)

    socket.close()
    context.term()
