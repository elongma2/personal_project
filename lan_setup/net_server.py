import json
import socket

class serverSocket():
    def __init__(self,bind_ip,port,):
        self.port = port
        self.bind_ip = bind_ip
        self.listen_socket = None
        self.clients = set()
        self.rx = {}

    def listen(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setblocking(False)
        self.listen_socket.bind((self.bind_ip, self.port))
        self.listen_socket.listen(5)
        print(f"Listening on {self.port}:{self.bind_ip}")
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
                new.append((conn,address))
                print(f"Accepted connection from {address}")
            except BlockingIOError:
                break
        return new
        
    def send_line(self,sock,obj:dict) -> json:
        json_string = json.dumps(obj) + "\n"
        try:
            sock.sendall(json_string.encode('utf-8'))
        except BlockingIOError as e:
            print(f"Error sending inputs: {e}")
            self.drop(sock)

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