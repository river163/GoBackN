import struct
import zlib

class PDU:
    HEADER_FORMAT = "!I1024sI"  # SeqNo(4B) + Data(1024B) + CRC(4B)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 1032 bytes

    def __init__(self, seq_no: int, data: bytes):
        self.seq_no = seq_no
        self.data = data.ljust(1024, b'\x00')[:1024]  # 确保数据长度固定
        self.crc = self._calculate_crc()

    def _calculate_crc(self) -> int:
        header = struct.pack("!I1024s", self.seq_no, self.data)
        return zlib.crc32(header)

    def encode(self) -> bytes:
        return struct.pack(self.HEADER_FORMAT, self.seq_no, self.data, self.crc)

    @classmethod
    def decode(cls, raw_data: bytes):
        if len(raw_data) != cls.HEADER_SIZE:
            return None
        try:
            seq_no, data, crc = struct.unpack(cls.HEADER_FORMAT, raw_data)
            temp_pdu = cls(seq_no, data)
            return temp_pdu if temp_pdu.crc == crc else None
        except struct.error:
            return None

    def is_corrupt(self) -> bool:
        return self.crc != self._calculate_crc()