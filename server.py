import os
import socket
import time
import random
from threading import Thread, Lock
from config import Configuration
from pdu import PDU

class Server:
    def __init__(self, config: Configuration):
        self.config = config
        self.host = "0.0.0.0"
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

    def _server_loop(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((self.host, self.port))
            print(f"Go-Back-N Server started on {self.host}:{self.port}")

            while self.running:
                data, addr = self.server_socket.recvfrom(1024)
                filename = data.decode().strip()
                print(f"Received request for '{filename}' from {addr}")

                if not os.path.exists(filename):
                    error_msg = f"ERROR:FILE_NOT_FOUND:{filename}"
                    self.server_socket.sendto(error_msg.encode(), addr)
                    continue

                Thread(target=self._handle_file_transfer, args=(filename, addr)).start()

        except Exception as e:
            if self.running:
                print(f"Server error: {e}")

    def _handle_file_transfer(self, filename: str, client_addr: tuple):
        try:
            # 读取文件并分块
            with open(filename, "rb") as f:
                file_data = f.read()
            chunks = [file_data[i:i+self.config.data_size] for i in range(0, len(file_data), self.config.data_size)]

            # Go-Back-N 参数
            base = self.config.init_seq_no
            next_seq = base
            window_size = self.config.sw_size
            pdus = [PDU(i, chunk) for i, chunk in enumerate(chunks)]
            total_pdus = len(pdus)
            last_ack = base - 1
            timer = None

            while base < total_pdus:
                # 发送窗口内的帧
                while next_seq < min(base + window_size, total_pdus):
                    if random.randint(1, 100) > self.config.lost_rate:  # 模拟丢包
                        pdu = pdus[next_seq]
                        self.server_socket.sendto(pdu.encode(), client_addr)
                        print(f"Sent PDU {next_seq} to {client_addr}")
                    next_seq += 1

                # 启动定时器
                if timer is None:
                    timer = time.time()

                # 接收 ACK
                try:
                    self.server_socket.settimeout(0.1)
                    ack_data, _ = self.server_socket.recvfrom(1024)
                    ack_seq = int(ack_data.decode())
                    print(f"Received ACK {ack_seq}")

                    if ack_seq >= base:
                        base = ack_seq + 1
                        timer = None  # 重置定时器

                except socket.timeout:
                    pass

                # 超时处理
                if timer and (time.time() - timer > self.timeout):
                    print(f"Timeout! Resending from {base}")
                    next_seq = base  # 回退到窗口起点
                    timer = None

            print(f"File {filename} transfer completed to {client_addr}")

        except Exception as e:
            print(f"Transfer error to {client_addr}: {e}")