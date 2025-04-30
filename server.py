import os
import socket
import threading


class Server:
    def __init__(self, config):
        self.config = config
        self.host = self._get_local_ip()
        self.port = config.udp_port
        self.server_socket = None
        self.running = False
        self.thread = None
        self.timeout = config.timeout / 1000

    def _get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return socket.gethostbyname(socket.gethostname())

    def _server_loop(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.host, self.port))
            print(f"Server started on {self.host}:{self.port}")

            while self.running:
                data, addr = self.server_socket.recvfrom(1024)
                filename = data.decode().strip()
                print(f"Request for '{filename}' from {addr}")

                if not os.path.exists(filename):
                    error_msg = f"ERROR:FILE_NOT_FOUND:{filename}"
                    self.server_socket.sendto(error_msg.encode(), addr)
                    continue

                try:
                    with open(filename, 'rb') as f:
                        content = f.read()
                        # 发送文件内容（假设文件较小可一次性发送）
                        self.server_socket.sendto(content, addr)
                        print(f"Sent '{filename}' to {addr}")
                except Exception as e:
                    error_msg = f"ERROR:{str(e)}"
                    self.server_socket.sendto(error_msg.encode(), addr)

        except Exception as e:
            if self.running:
                print(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._server_loop)
            self.thread.start()
            print("Server running in background")

    def stop(self):
        if self.running:
            self.running = False
            if self.server_socket:
                self.server_socket.close()
            self.thread.join()
            print("Server stopped")