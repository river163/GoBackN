import os
import socket
import time
import random
from threading import Thread, Lock
from config import Configuration
from pdu import PDU
//
class Server:
    def __init__(self, config: Configuration):
        self.config = config
        self.host = self._get_local_ip()
        self.port = config.udp_port
        self.server_socket = None
        self.running = False
        self.lock = Lock()
        self.timeout = config.timeout / 1000  # 转换为秒

    def start(self):
        self.running = True
        Thread(target=self._server_loop, daemon=True).start()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def _get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "0.0.0.0"

    def _server_loop(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.host, self.port))
            print(f"🖥️ Go-Back-N Server started on {self.host}:{self.port}")

            while self.running:
                try:
                    data, addr = self.server_socket.recvfrom(1024)
                    filename = data.decode().strip()
                    print(f"📥 Received request for '{filename}' from {addr}")
                    Thread(target=self._handle_file_transfer, args=(filename, addr)).start()
                except OSError:
                    break

        except Exception as e:
            if self.running:
                print(f"❌ Server error: {e}")
        finally:
            self.server_socket.close()

    def _handle_file_transfer(self, filename: str, client_addr: tuple):
        try:
            if not os.path.exists(filename):
                error_msg = f"ERROR:FILE_NOT_FOUND:{filename}"
                self.server_socket.sendto(error_msg.encode(), client_addr)
                return

            with open(filename, "rb") as f:
                file_data = f.read()

            # 分块并填充数据
            chunks = []
            for i in range(0, len(file_data), self.config.data_size):
                chunk = file_data[i:i+self.config.data_size]
                if len(chunk) < self.config.data_size:
                    chunk += b'\x00' * (self.config.data_size - len(chunk))
                chunks.append(chunk)

            total_pdus = len(chunks)
            window_size = self.config.sw_size
            base = 0
            next_seq_num = 0
            timer = None

            while base < total_pdus:
                # 发送窗口内的数据包
                while next_seq_num < min(base + window_size, total_pdus):
                    if random.randint(1, 100) > self.config.lost_rate:
                        pdu = PDU(next_seq_num, chunks[next_seq_num])
                        self.server_socket.sendto(pdu.encode(), client_addr)
                        print(f"📤 Sent PDU {next_seq_num} to {client_addr}")
                    next_seq_num += 1

                # 设置超时计时器
                if timer is None:
                    timer = time.time()

                # 等待ACK
                try:
                    self.server_socket.settimeout(0.1)
                    ack_data, _ = self.server_socket.recvfrom(1024)
                    ack_num = int(ack_data.decode())
                    print(f"📨 Received ACK {ack_num}")

                    if ack_num >= base:
                        base = ack_num + 1
                        next_seq_num = base
                        timer = None

                except (socket.timeout, ValueError):
                    pass

                # 超时处理
                if timer and (time.time() - timer > self.timeout):
                    print(f"⏰ Timeout! Resending from {base}")
                    next_seq_num = base
                    timer = None

            print(f"✅ File {filename} transfer completed to {client_addr}")

        except Exception as e:
            print(f"❌ Transfer error to {client_addr}: {e}")