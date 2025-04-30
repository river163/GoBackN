from configparser import ConfigParser

class Configuration:
    def __init__(self, config_file: str):
        parser = ConfigParser()
        """从配置文件加载协议参数"""
        # 手动读取文件并指定编码
        with open(config_file, 'r', encoding='utf-8') as f:
            parser.read_file(f)

        network = parser["Network"]
        self.udp_port = int(network["UDPPort"])
        self.data_size = int(network["DataSize"])
        self.error_rate = int(network["ErrorRate"])
        self.lost_rate = int(network["LostRate"])
        self.sw_size = int(network["SWSize"])
        self.init_seq_no = int(network["InitSeqNo"])
        self.timeout = int(network["Timeout"])