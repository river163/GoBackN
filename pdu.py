import struct
import zlib


class PDU:
    HEADER_FORMAT = "!I1024sI"  # SeqNo(4B) + Data(1024B) + CRC(4B)

    def __init__(self, seq_no: int, data: bytes):
        self.seq_no = seq_no
        self.data = data
        self.crc = self._calculate_crc()

    def _calculate_crc(self) -> int:
        header = struct.pack("!I1024s", self.seq_no, self.data)
        return zlib.crc32(header)

    def encode(self) -> bytes:
        return struct.pack(self.HEADER_FORMAT, self.seq_no, self.data, self.crc)

    @classmethod
    def decode(cls, raw_data: bytes) -> 'PDU':
        seq_no, data, crc = struct.unpack(cls.HEADER_FORMAT, raw_data)
        pdu = cls(seq_no, data)
        return pdu if pdu.crc == crc else None  # 返回 None 表示校验失败

    def is_corrupt(self) -> bool:
        return self.crc != self._calculate_crc()