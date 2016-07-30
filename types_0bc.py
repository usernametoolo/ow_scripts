
class Key:
    @staticmethod
    def getTypeFromKeyBits(key):
        num = (key >> 48);
        num = (((num >> 1) & 0x55555555) | ((num & 0x55555555) << 1));
        num = (((num >> 2) & 0x33333333) | ((num & 0x33333333) << 2));
        num = (((num >> 4) & 0x0F0F0F0F) | ((num & 0x0F0F0F0F) << 4));
        num = (((num >> 8) & 0x00FF00FF) | ((num & 0x00FF00FF) << 8));
        num = ((num >> 16) | (num << 16));
        num >>= 20;
        return num + 1;

    def __init__(self, bd):
        self.typeId = 0
        self.index = 0
        self.ident = 0
        if bd:
            self.read(bd)

    def read(self, bd):
        keyBytes = [0] * 8
        for i in range(8):
            keyBytes[7 - i] = bd.readU8()
        value = 0
        for b in keyBytes:
            value = (value << 8) | b

        self.typeId = Key.getTypeFromKeyBits(value)
        self.index = value & 0xFFFFFFFFFFFF
        self.ident = (value >> 32) & 0xFFFF

    def __str__(self):
        return '{:012x}.{:03x}'.format(self.index, self.typeId)

    def __repr__(self):
        return str(self)



class CommonRecordHeader:
    headerSize = 16 + 2 + 2 + 4

    def __init__(self, bd):
        self.guid = '00000000000000000000000000000000'
        self.unk = 0
        self.type = 0
        self.recordSize = 0
        self.recordStartOffset = 0
        if bd:
            self.read(bd)

    def read(self, bd):
        self.recordStartOffset = bd.tell()
        self.guid = bd.readHex(16)
        val = 0
        self.unk = bd.readU16BE()
        self.type = bd.readU16BE()
        self.recordSize = bd.readU32()

    def __str__(self):
        return '{0} {1:04x} {2:04x} {3}'.format(self.guid, self.unk, self.type, self.recordSize)




