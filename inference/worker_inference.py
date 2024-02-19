import json
import time

import numpy as np
import zmq


# Port on which we send the live myo data to inference engine
LIVE_PUB_PORT = 55512
# Port on which we receive the inference result
INFERENCE_RESULT_PORT = 55511
# Visualiser input port
VISUALISER_PORT = 55516

context = zmq.Context()

def worker_myo_receiver(q_myo, q_myo_imu, q_terminate):
    """
    Receive processed myo data and send it to INFERENCE
    :param q_myo: sEMG signals
    :param q_terminate:
    :return:
    """
    # New temp pub socket
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(f"tcp://127.0.0.1:{LIVE_PUB_PORT}")
    time.sleep(0.2)

    last_imu = None

    while q_terminate.empty():
        while not q_myo.empty():
            # print("Myo data: ", q_myo.get())

            emg_data = q_myo.get()[:8]
            while not q_myo_imu.empty():
                last_imu = q_myo_imu.get()[:10]

            emg_data.extend(last_imu)
            send_data = {"from_file": False, "data": emg_data}
            js = json.dumps(send_data).encode('utf-8')
            pub_socket.send(js)
            continue

        time.sleep(0.001)

    # Kill the pub socket
    pub_socket.close()
    print("Myo worker finished.")


def worker_inference_res_to_visualiser(q_terminate):
    """
    Take inference results and send them to the visualiser
    :param q_inference_res:
    :param q_terminate:
    :return:
    """
    sub_from_inference = context.socket(zmq.SUB)
    sub_from_inference.connect(f"tcp://127.0.0.1:{INFERENCE_RESULT_PORT}")
    sub_from_inference.subscribe("")

    pub_to_visualiser = context.socket(zmq.PUB)
    pub_to_visualiser.bind(f"tcp://127.0.0.1:{VISUALISER_PORT}")
    time.sleep(0.2)

    while q_terminate.empty():
        result = sub_from_inference.recv()
        result = json.loads(result.decode("utf-8"))

        data = result["data"]
        shape = result["shape"]
        print("Received inference result with shape:", shape)

        # Send to visualiser
        out = json.dumps(data).encode("utf-8")
        pub_to_visualiser.send(out)

    sub_from_inference.close()
    pub_to_visualiser.close()

    print("Inference-visualiser bridge worker finished.")

