import socket
import os
from pathlib import Path

class Client:
    def __init__(self):
        # 创建 download 目录（如果不存在）
        self.download_dir = "download"
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)

    def request_file(self, server_ip, server_port, filename):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(filename.encode(), (server_ip, server_port))
                s.settimeout(5)  # 设置超时时间

                data, _ = s.recvfrom(65535)  # 接收最大可能的UDP包

                # 尝试解码判断是否是错误消息
                try:
                    response = data.decode()
                    if response.startswith("ERROR:"):
                        print(response)
                        return
                except UnicodeDecodeError:
                    pass  # 继续保存为二进制文件

                # 保存到 download 目录
                save_path = os.path.join(self.download_dir, filename)  # 关键修改点
                with open(save_path, 'wb') as f:
                    f.write(data)
                print(f"File '{filename}' saved to {save_path}")

        except socket.timeout:
            print("Error: Request timed out. No response from server.")
        except Exception as e:
            print(f"Error: {str(e)}")