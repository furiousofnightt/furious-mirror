class ControlChannel:
    def __init__(self, socket):
        self.socket = socket

    def recv(self, size):
        return self.socket.recv(size)

    def send(self, data):
        self.socket.sendall(data)
