import os
import socket
import random
from pathlib import Path
from config import Configuration
from pdu import PDU

class Client:
    def __init__(self, config: Configuration):
        self.config = config
        self.download_dir = "download"
        Path(self.download_dir).mkdir(exist_ok=True)

    def request_file(self, server_ip: str, server_port: int, filename: str):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(filename.encode(), (server_ip, server_port))

            expected_seq = self.config.init_seq_no
            received_data = bytearray()
            last_ack = expected_seq - 1

            while True:
                try:
                    data, _ = sock.recvfrom(65535)
                    pdu = PDU.decode(data)

                    # 模拟帧错误
                    if pdu is None or random.randint(1, 100) <= self.config.error_rate:
                        print("Simulated packet corruption/drop")
                        continue

                    # 按序接收
                    if pdu.seq_no == expected_seq:
                        received_data.extend(pdu.data.rstrip(b'\x00'))  # 去除填充
                        expected_seq += 1
                        last_ack = pdu.seq_no
                        print(f"Received PDU {pdu.seq_no}")
                    else:
                        print(f"Out-of-order PDU {pdu.seq_no}, expecting {expected_seq}")

                    # 发送 ACK（可能丢失）
                    if random.randint(1, 100) > self.config.lost_rate:
                        sock.sendto(str(last_ack).encode(), (server_ip, server_port))

                except socket.timeout:
                    print("No more data, transfer completed")
                    break

            # 保存文件
            save_path = os.path.join(self.download_dir, filename)
            with open(save_path, "wb") as f:
                f.write(received_data)
            print(f"File saved to {save_path}")

        except Exception as e:
            print(f"Error: {str(e)}")