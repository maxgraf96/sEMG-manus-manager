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
        # Parse: we have 20 floats in a message
        finger_data = struct.unpack('20f', message[0:80])

        # At position 20 we have the timestamp
        timestamp = struct.unpack('q', message[80:88])

        data = list(finger_data)

        data.append(timestamp[0])

        # Add to the queue
        q.put(data)


    socket.close()
    context.term()