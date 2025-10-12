# lan_setup/net_client.py
import socket, json, time

class clientSocket:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.closed = False
        self._rx = b""
        self._tx = bytearray()
    def connect(self):
        # Try once; if it fails, leave socket=None and closed=True so caller can handle it
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.setblocking(False)
            self.socket = s
            self.closed = False
            print(f"Connected to {self.host}:{self.port}")
        except socket.error as e:
            print(f"Error connecting to {self.host}:{self.port}: {e}")
            self.socket = None
            self.closed = True

    def is_connected(self):
        return (self.socket is not None) and (not self.closed)

    def send_line(self, obj: dict):
        if not self.is_connected():
            return
        try:
            self._tx += (json.dumps(obj) + "\n").encode("utf-8")
        except socket.error as e:
            print(f"Enqueue error: {e}")
            self.closed = True
    
    def flush(self):    
        if not self.is_connected():
            return
        try:
            send = self.socket.send(self._tx)
            if send > 0:
                del self._tx[:send]
        except (InterruptedError,BlockingIOError) as e: 
            pass
        except OSError as e:
            print(f"Error sending: {e}")
            self.closed = True

    def poll_lines(self):
        # If not connected, nothing to read
        if not self.is_connected():
            return []
        try:
            chunk = self.socket.recv(4096)
            if not chunk:
                # Peer closed
                self.closed = True
                return []
            self._rx += chunk
        except BlockingIOError:
            return []
        except socket.error as e:
            print(f"Error receiving: {e}")
            self.closed = True
            return []

        lines = []
        while b"\n" in self._rx:
            line, self._rx = self._rx.split(b"\n", 1)
            if not line:
                continue
            try:
                lines.append(json.loads(line.decode("utf-8")))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON line: {e}")
        return lines

    def close(self):
        try:
            if self.socket:
                self.socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")
        finally:
            self.socket = None
            self.closed = True
