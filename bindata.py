import struct


class BinData(object):
    def __init__(self, data):
        self.data = data
        self.offset = 0

        self.unpackers = dict()
        pass

    def getUnpacker(self, fmt):
        if fmt in self.unpackers:
            return self.unpackers[fmt]
        unpacker = struct.Struct(fmt)
        self.unpackers[fmt] = unpacker
        return unpacker

    def unpack_nocache(self, fmt):
        size = struct.calcsize(fmt)
        result = struct.unpack_from(fmt, self.data, self.offset)
        self.offset = self.offset + size
        return result

    def unpack(self, fmt):
        unpacker = self.getUnpacker(fmt)
        try:
            result = unpacker.unpack_from(self.data, self.offset)
            self.offset = self.offset + unpacker.size
            return result
        except struct.error as err:
            print(err)
            return (None,)
        

    def unpack_one(self, fmt):
        return self.unpack(fmt)[0]

    def readU8(self): return self.unpack_one('B')
    def readI8(self): return self.unpack_one('b')
    def readU16(self): return self.unpack_one('H')
    def readI16(self): return self.unpack_one('h')
    def readU32(self): return self.unpack_one('I')
    def readI32(self): return self.unpack_one('i')
    def readU64(self): return self.unpack_one('Q')
    def readI64(self): return self.unpack_one('q')

    def readF32(self): return self.unpack_one('f')
    def readF64(self): return self.unpack_one('d')

    def read2F32(self): return self.unpack('2f')
    def read3F32(self): return self.unpack('3f')
    def read4F32(self): return self.unpack('4f')

    def read2U32(self): return self.unpack('2I')
    def read3U32(self): return self.unpack('3I')
    def read4U32(self): return self.unpack('4I')

    def read2I32(self): return self.unpack('2i')
    def read3I32(self): return self.unpack('3i')
    def read4I32(self): return self.unpack('4i')

    def readU16BE(self): return self.unpack_one('>H')
    def readU32BE(self): return self.unpack_one('>I')
    def readU64BE(self): return self.unpack_one('>Q')

    def readCStr(self): 
        res = []
        while True:
            s = self.unpack_one('1s')
            if s == '\0': break
            res.append(s)
        return res.join()

    def readStr(self, size):
        return unpack_nocache('{}s'.format(size))[0]

    def tell(self): return self.offset
    
    def seekCur(self, offset): self.offset = self.offset + offset
    def seekSet(self, offset): self.offset = offset
    def seekEnd(self, offset): self.offset = len(self.data) + offset

    def dataSize(self): return len(self.data)

    def readHex(self, size): 
        res = self.unpack('{}B'.format(size))
        return ''.join(['{:02x}'.format(v) for v in res])
        # return ['{:02x}'.format(v) for v in res]