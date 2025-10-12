import json
import socket

class serverSocket():
    def __init__(self,bind_ip,port,):
        self.port = port
        self.bind_ip = bind_ip
        self.listen_socket = None
        self.clients = set()
        self.rx = {}
        self.tx = {}
    def listen(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setblocking(False)
        self.listen_socket.bind((self.bind_ip, self.port))
        self.listen_socket.listen(64)
        print(f"Listening on {self.bind_ip}:{self.port}")
        return self.listen_socket
    
    def accept_new(self) -> list:
        new = []
        if not self.listen_socket: return new
        while True:
            try:
                conn,address = self.listen_socket.accept()
                conn.setblocking(False)
                self.clients.add(conn)
                self.rx[conn] = b""
                self.tx[conn] = bytearray() #array of bytes
                new.append((conn,address))
                print(f"Accepted connection from {address}")
            except BlockingIOError:
                break
        return new
        
    def send_line(self,sock,obj:dict) -> None:
        try:
            line = (json.dumps(obj) + "\n").encode('utf-8')
            self.tx[sock] += line
        except BlockingIOError as e:
            print(f"Error sending inputs: {e}")
            self.drop(sock)
    
     # --- try to flush pending bytes for all clients ---
    def flush_bytes(self):
        dead = []
        for client in list(self.clients):
            buffer = self.tx[client]
            if not buffer: continue
            try:
                send = client.send(buffer) #send return number of bytes sent
                if send > 0:
                    del buffer[:send]
                else:
                    pass
            except (InterruptedError,BlockingIOError) as e:
                continue
            except OSError as e:
                print(f"Error sending inputs: {e}")
                dead.append(client)
        for client in dead:
            self.drop(client)

    def broadcast(self,obj:dict) -> None:
        dead = []
        for client in list(self.clients):
            try:
                self.send_line(client,obj)
            except socket.error as e:
                print(f"Error sending inputs: {e}")
                dead.append(client)
        for client in dead:
            self.drop(client)
            
    def poll_lines(self,socket) -> list[dict]:
        try:
            chunk = socket.recv(1024)
            if not chunk:
                self.drop(socket)
                return []
            self.rx[socket] += chunk
        except BlockingIOError as e:
            return []
        lines = []
        while b"\n" in self.rx[socket]:
            line,self.rx[socket] = self.rx[socket].split(b"\n",1)
            if not line: continue
            try:
                lines.append(json.loads(line.decode('utf-8')))
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        return lines
        
    def drop(self,socket) -> None:
        try:
            if socket in self.clients:
                self.clients.remove(socket)
            if socket in self.rx:
                del self.rx[socket]
            if socket in self.tx:
                del self.tx[socket]
            socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")
    
    def close(self):
        for client in list(self.clients):
            self.drop(client)
        try:
            if self.listen_socket:
                self.listen_socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")