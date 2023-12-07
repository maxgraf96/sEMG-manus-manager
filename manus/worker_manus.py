
def worker_manus(q):
    # TODO: receive data from Manus

    def add_to_queue(emg, movement):
        q.put(emg)

    # Worker function
    while True:
        m.run()