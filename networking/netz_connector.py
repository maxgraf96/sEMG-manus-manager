import socket


def listen_for_netz_finished_process(q_finished):
    """
    Listen for the Netz finished event through UDP
    :param q_finished: the queue to put the finished event into
    :return:
    """

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind the socket to the port
    server_address = ('', 12345)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)

    while True:
        print('\nwaiting to receive message')
        data, address = sock.recvfrom(4096)

        print('received {} bytes from {}'.format(len(data), address))
        print(data)

        if data == b'netz_finished':
            q_finished.put(True)
            break
        else:
            print('received unknown message')
            break

    print('closing netz socket')
    sock.close()