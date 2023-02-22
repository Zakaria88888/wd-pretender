import io

from ctypes import memmove, sizeof, pointer, Structure, c_uint32

from core.utils import *
from core.signatures import Signatures

class RMDX:
    class Header(Structure):
        _fields_ = [
            ("Signature", c_uint32),
            ("Timestamp", c_uint32),
            ("Unknown1", c_uint32),
            ("Options", c_uint32),
            ("Unknown2", c_uint32),
            ("Unknown3", c_uint32),
            ("CompressedDataOffset", c_uint32),
            ("DecompressedDataSize", c_uint32),
            ("UnknownArray", c_uint32 * 8)
        ]

    class CompressedDataHeader(Structure):
        _fields_ = [
            ("CompressedSize", c_uint32),
            ("CompressedCrc", c_uint32),
        ]

    def __init__(self, stream: io.BytesIO) -> None:
        self.header = RMDX.Header()
        self.unknown_data = b''
        self.compress_header = RMDX.CompressedDataHeader()

        self.stream = stream
        self.__init_from_stream(stream)
        self.signatures_bytes = self.__extract_signatures()
        self.signatures_stream = io.BytesIO(self.signatures_bytes)

    def update(self, signatures: Signatures):
        self.header.DecompressedDataSize = signatures.length
        self.cdata = compress(signatures.stream.read())
        self.compress_header.CompressedSize = len(self.cdata)
        self.compress_header.CompressedCrc = compute_crc32(io.BytesIO(self.cdata))

    def validate_crc(self) -> bool:
        compressed_data = io.BytesIO(self.cdata)
        return self.cdata_header.CompressedCrc == compute_crc32(compressed_data)
    
    def pack(self):
        header = bytes(self.header)
        cheader = bytes(self.compress_header)
        return header + self.unknown_data + cheader + self.cdata

    def __init_from_stream(self, stream: io.BytesIO):
        buffer = stream.read(0x40)
        memmove(pointer(self.header), buffer, sizeof(self.header))

        compress_offset = self.header.CompressedDataOffset
        self.unknown_data = stream.read(compress_offset - 0x40)
        
        buffer = stream.read(8)
        memmove(pointer(self.compress_header), buffer, sizeof(self.compress_header))
        self.cdata = stream.read(self.compress_header.CompressedSize)
    
    def __extract_signatures(self) -> bytes:
        return decompress(self.cdata)
