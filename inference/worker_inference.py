import json
import time
import onnxruntime as ort

import numpy as np
import zmq


# Port on which we send the live myo data to inference engine
LIVE_PUB_PORT = 55512
# Port on which we receive the inference result
INFERENCE_RESULT_PORT = 55511
# Visualiser input port
VISUALISER_PORT = 55516

context = zmq.Context()


d_model = 32
d_state = 32
n_layers = 6
config = {
    "d_model": d_model,
    "n_layers": n_layers,
    "d_state": d_state,
    "d_inner": 2 * d_model,
    "d_conv": 4,
}


def worker_myo_receiver(q_myo, q_terminate):
    """
    Receive processed myo data and send it to INFERENCE
    :param q_myo: sEMG signals
    :param q_terminate:
    :return:
    """
    # New temp pub socket
    # pub_socket = context.socket(zmq.PUB)
    # pub_socket.bind(f"tcp://127.0.0.1:{LIVE_PUB_PORT}")

    pub_to_bridge = context.socket(zmq.PUB)
    pub_to_bridge.bind(f"tcp://127.0.0.1:{INFERENCE_RESULT_PORT}")

    time.sleep(0.2)

    # Load onnx model
    onnx_model_path = "resources/model.onnx"
    ort_session = ort.InferenceSession(onnx_model_path)

    x = np.random.randn(1, 8) * 10
    hs = np.zeros((5, config["n_layers"], 1, config["d_inner"], config["d_state"]))
    inputs = np.zeros(
        (5, config["n_layers"], 1, config["d_inner"], config["d_conv"] - 1)
    )

    x = np.float32(x)
    hs = np.float32(hs)
    inputs = np.float32(inputs)

    switch = True
    while q_terminate.empty():
        while not q_myo.empty():
            # print("Myo data: ", q_myo.get())

            emg_data = q_myo.get()
            emg_data = emg_data[:8]
            emg_data = np.abs(np.array(emg_data))

            # if not switch:
            # switch = not switch
            # continue

            output = ort_session.run(
                None,
                {
                    "x": np.float32(np.expand_dims(emg_data, 0)),
                    "hs.3": hs,
                    "inputs.3": inputs,
                },
            )

            out = output[0]
            hs = output[1]
            inputs = output[2]
            # print(out[0][5])

            # counter += 1
            # if counter % 10 != 0:
            # continue
            # else:
            # counter = 0

            # js = json.dumps(send_data).encode("utf-8")
            # pub_socket.send(js)
            pub_to_bridge.send(
                json.dumps({"data": out.tolist(), "shape": out.shape}).encode("utf-8")
            )

            switch = not switch

        time.sleep(0.001)

    # Kill the pub socket
    pub_to_bridge.close()
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
        # print("Received inference result with shape:", shape)

        # Send to visualiser
        out = json.dumps(data).encode("utf-8")
        pub_to_visualiser.send(out)

    sub_from_inference.close()
    pub_to_visualiser.close()

    print("Inference-visualiser bridge worker finished.")
