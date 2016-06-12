from collections import namedtuple, OrderedDict
from pprint import pprint
import types
from tabulate import tabulate 
import math
import os
from pathlib import Path

from utils import recordclassdef, expectValue
from bindata import BinData
import obj_file

ProcessingContext = recordclassdef('ProcessingContext', ['header', 'filename', 'filepath', 'exportPath', 'expectedFormat'])
Header0BC = recordclassdef('Header0BC', ['countRecords', 'sizeRecords', 'offsetToSomething', 'maybeDataType'])

def readHeader0BC(bd):
    h = Header0BC()
    h.countRecords = bd.readU32()
    h.sizeRecords = bd.readU32()
    h.offsetToSomething = bd.readU32()
    h.maybeDataType = bd.readU32()
    return h


PhysHeader = recordclassdef('PhysHeader', ['unkOffset1', 'unkOffset2', 'unkOffset3', 'physFooterOffset'])

PhysFooter = recordclassdef('PhysFooter', ['bboxesDataOffset', 'verticesOffset', 'facesOffset', 'countBboxes', 'countVertices', 'countFaces', 'unk'])


# Key = recordclassdef('Key', ['typeId', 'ident', 'index'])

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

def sumSqr(vals):
    return sum(map(lambda x: x*x, vals))




def readPhysicalCollision0BC(bd, context):
    print('readPhysicalCollision0BC')

    def readPhysHeader(bd):
        ph = PhysHeader()
        ph.unkOffset1 = bd.readU64()
        ph.unkOffset2 = bd.readU64()
        ph.unkOffset3 = bd.readU64()
        ph.physFooterOffset = bd.readU64()
        return ph

    def readFooter(bd):
        f = PhysFooter()
        f.bboxesDataOffset = bd.readU64()
        f.verticesOffset = bd.readU64()
        f.facesOffset = bd.readU64()
        print('bboxesDataOffset = {:x}'.format(f.bboxesDataOffset))
        print('verticesOffset = {:x}'.format(f.verticesOffset))
        print('facesOffset = {:x}'.format(f.facesOffset))

        print('pos after offsets = {:x}'.format(bd.tell()))

        f.countBboxes = bd.readU32()
        f.countVertices = bd.readU32()
        f.countFaces = bd.readU32()

        print('countBboxes = {:x}'.format(f.countBboxes))
        print('countVertices = {:x}'.format(f.countVertices))
        print('countFaces = {:x}'.format(f.countFaces))

        print('after vertices = {:x}'.format(f.verticesOffset + f.countVertices*4*4))
        print('after bboxesData = {:x}'.format(f.bboxesDataOffset + f.countBboxes*4*8))
        print('after faces = {:x}'.format(f.facesOffset + f.countFaces*32))


        f.unk = []
        for i in range(15):
            f.unk.append(bd.readU32())

        print(f)

        return f

    def readVertices(bd, footer):
        bd.seekSet(footer.verticesOffset)
        print('readVertices begin offset = {:x}'.format(bd.tell()))
        verts = []
        for i in range(footer.countVertices):
            verts.append(bd.read4F32())
            assert(verts[-1][3] == 0.0)
        print('readVertices end offset = {:x}'.format(bd.tell()))
        return verts

    def readFaces(bd, footer):
        bd.seekSet(footer.facesOffset)
        print('readFaces begin offset = {:x}'.format(bd.tell()))
        faces = []
        for i in range(footer.countFaces):
            row = []
            for j in range(8):
                row.append(bd.readI32())
            faces.append(row)
        print('readFaces end offset = {:x}'.format(bd.tell()))

        # for idx in faces:
        #     print(idx)

        # print(tabulate(faces))

        return faces

    def readBboxesData(bd, footer):
        bd.seekSet(footer.bboxesDataOffset)
        print('readBboxesData begin offset = {:x}'.format(bd.tell()))
        bboxesData = []
        for i in range(footer.countBboxes):
            s = []
            for i in range(6):
                s.append(bd.readF32())
            s.append(bd.readU32())
            s.append(bd.readU32())
            bboxesData.append(s)
        print('readBboxesData end offset = {:x}'.format(bd.tell()))

        # for idx in faces:
        #     print(idx)

        #print(tabulate(bboxesData))

        return bboxesData

    def exportPhysGeo(context, verts, faces):
        path = context.exportPath / (context.filename + '.phys_geo.obj')
        print('exportPhysGeo', str(path))
        # with open(path, 'w') as f:
        with path.open(mode='w') as f:
            obj_file.writeHeader(f)
            obj_file.writeVertices(f, verts)
            obj_file.writeTrigIndices(f, faces)

    assert(bd.tell() == 0x10)
    ph = readPhysHeader(bd)

    assert(bd.dataSize() > ph.physFooterOffset)
    bd.seekSet(ph.physFooterOffset)
    footer = readFooter(bd)

    verts = readVertices(bd, footer)
    faces = readFaces(bd, footer)

    exportPhysGeo(context, verts, faces)


    pass


def readRecords0BC_format_12(bd, context):
    print('readRecords0BC_format_12')

    tab = []
    for i in range(context.header.countRecords):
        row = []
        row.append(bd.readHex(16))
        row.append(Key(bd))

        expectValue(row[-1].typeId, 0x055, "format 0x12 references {} instead .055".format(row[-1]))

        tab.append(row)

    print(tabulate(tab, floatfmt='.6'))
    pass

def readRecords0BC(bd, context):
    print('readRecords0BC')

    if 0x0 <= context.expectedFormat and context.expectedFormat < 0x10:
        if context.header.sizeRecords == 0:
            print('nothing to read, size == 0')
            return

    if context.expectedFormat == 0x10:
        print('unknown format 0x10 - it is usually physical collision model')
        return

    if context.expectedFormat > 0x10:
        print('might be an unknown format')
        return


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

    class Format_Unk:
        @staticmethod
        def read(bd, row, recHeader):
            # print('Reading unknown format', hex(recHeader.type))

            columnCount = (recHeader.recordSize - CommonRecordHeader.headerSize) // 4

            readMore = 0
            if columnCount > 50:
                readMore = columnCount - 50
                columnCount = 50

            for j in range(0, columnCount):
                row.append(bd.readF32())

            bd.seekCur(readMore * 4)
            pass

        @staticmethod
        def dump(tab, context):
            pass

    def dumpRecordPoints(points, nameSuffix, context):
        path = context.exportPath / (context.filename + nameSuffix)
        print('dumpRecordPoints', str(path))
        with path.open(mode='w') as f:
            obj_file.writeHeader(f)
            obj_file.writeVertices(f, points)


    class Format_01:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize >= 160)

            tmp = []

            row.append(Key(bd))          # keyRef00c, reference to .00c
            row.append(bd.readU32())     # unkCount1
            unkCount1 = row[-1]
            row.append(bd.readU32())     # unkCount2
            unkCount2 = row[-1]
            row.append(bd.readHex(4))    # unk bitmask
            row.append(bd.read2F32())    # unkFloats1, big range
            row.append(bd.readF32())     # unkFloat2
            # 56
            # print(bd.tell() - recHeader.recordStartOffset)
            row.append(Key(bd))         # keyRef01a reference to .01a
            row.append(bd.readU32())    # unk size?
            unkSize = row[-1]
            row.append(bd.readU32())    # unk count3?
            unkCount3 = row[-1]
            assert(unkCount3 <= unkCount2)
            row.append(bd.read3F32())  # pos
            row.append(bd.read3F32())  # scl
            row.append(bd.read4F32())  # quat
            for i in range(7): row.append(bd.readHex(4)) # unkBitmask2
            for i in range(5): row.append(bd.readI32())  # unkInts

            if unkCount2 > 1:
                tmp.append(bd.read3F32())  # pos
                tmp.append(bd.read3F32())  # scl
                tmp.append(bd.read4F32())  # quat
                
                # for i in range(7): row.append(bd.readHex(4))
                # for i in range(5): row.append(bd.readI32())

                # for i in range(7): row.append(bd.readHex(4))
                # for i in range(10): row.append(bd.readF32())




            bd.seekSet(recHeader.recordStartOffset + recHeader.recordSize)

            pass

        @staticmethod
        def dump(tab, context):
            verts = [row[10] for row in tab]
            dumpRecordPoints(verts, '.points_001.obj', context)
            pass


    class Format_02_08:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 96)
            columnCount = 96 // 4

            # def, keyMdl, keyMtl, scl?, pos, quat, unk_4u32

            row.append(Key(bd)) # keyRef00c
            row.append(Key(bd)) # keyRef01a
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat
            row.extend(bd.read4U32()) # unk 4 u32

            expectValue(row[1].typeId, 0x00c, "format 0x02 or 0x08 references {} instead .00c".format(row[1]))
            expectValue(row[2].typeId, 0x01a, "format 0x0c or 0x08 references {} instead .01a".format(row[2]))

        @staticmethod
        def dump(tab, context):
            verts = [row[3] for row in tab]
            dumpRecordPoints(verts, '.points_002_008.obj', context)
            pass

    class Format_03:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 64)
            row.append(bd.read4F32()) # quat
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # unk, bboxMax?

        @staticmethod
        def dump(tab, context):
            verts = [row[2] for row in tab]
            dumpRecordPoints(verts, '.points_003.obj', context)
            pass


    class Format_04:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 192)
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat
            row.append(bd.read3F32()) # pos2?
            row.append(bd.read3F32()) # scl2?
            row.append(bd.read4F32()) # quat2?
            row.append(bd.read3F32()) # unk, bboxMax?
            row.append(bd.readU32())  # unk2
            expectValue(row[-1], 0, "format 04, unk2")
            row.append(Key(bd))       # key1, reference .004
            expectValue(row[-1].typeId, 0x004, "format 04 key1 reference to {}".format(row[-1]))
            row.append(Key(bd))       # key2, referemce .004
            expectValue(row[-1].typeId, 0x004, "format 04 key2 reference to {}".format(row[-1]))
            row.append(bd.readU32())  # unk3
            row.append(bd.readU32())  # unk4
            for i in range(7): row.append(bd.readF32()) # unk5
            for i in range(5): row.append(bd.readI32()) # unk6

        @staticmethod
        def dump(tab, context):
            verts = [row[1] for row in tab]
            dumpRecordPoints(verts, '.points_004.obj', context)
            pass

    class Format_07:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 88)

            # placements of scripts/voice lines/localization closed captions?

            for i in range(4): row.append(bd.readF32()) # unk0
            row.append(bd.read3F32()) # pos
            row.append(bd.readU32())  # unk1
            expectValue(row[-1], 0, "format 07, unk1")
            row.append(Key(bd))       # key1, reference .0a9
            row.append(Key(bd))       # key2, reference .0aa
            row.append(Key(bd))       # key3, reference .008

            row.append(bd.readF32())  # unk2
            row.append(bd.readU32())  # unk3
            expectValue(row[-1], 0, "format 07, unk3")


        @staticmethod
        def dump(tab, context):
            verts = [row[5] for row in tab]
            dumpRecordPoints(verts, '.points_007.obj', context)
            pass

    class Format_09:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 200)
            columnCoount = 200 // 4

            row.append(bd.read4F32()) # quat 
            row.append(bd.read3F32()) # pos
            for i in range(13, 15): row.append(bd.readU32())    # unk1
            row.append(bd.readHex(4))                           # unk2
            for i in range(16, 19): row.append(bd.readU32())    # unk3
            for i in range(19, 29): row.append(bd.readF32())    # unk4
            for i in range(29, 30): row.append(bd.readHex(4))   # unk5
            for i in range(30, 37): row.append(bd.readI32())    # unk6
            for i in range(37, 43): row.append(bd.readF32())    # unk7
            for i in range(43, 50): row.append(bd.readI32())    # unk8

        @staticmethod
        def dump(tab, context):
            verts = [row[2] for row in tab]
            dumpRecordPoints(verts, '.points_009.obj', context)
            pass

    class Format_0A:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize >= 88)

            valuesCount = bd.readU32()
            assert(valuesCount >= 1)
            row.append(valuesCount)
            row.append(bd.readU32())                 # unk1
            expectValue(row[-1], 0, "format 0a")
            row.append(bd.readU32())                 # unk2
            expectValue(row[-1], 24, "format 0a")

            valuesSize1 = bd.readU32()
            valuesSize2 = bd.readU32()
            expectValue(valuesSize1, valuesSize2, "format 0a, unexpected sizes")
            row.append(valuesSize1)
            row.append(valuesSize2)
            row.append(bd.readU32())                 # unk3
            expectValue(row[-1], 1, "format 0a")

            # values = row
            values = []
            for i in range(valuesCount):
                value = []
                value.append(bd.read4F32()) # quat
                value.append(bd.read3F32()) # pos
                value.append(bd.read3F32()) # scl? always positive?
                values.append(value)
            row.append(values)

        @staticmethod
        def dump(tab, context):
            verts = []
            for row in tab:
                for values in row[7]:
                    verts.append(values[1])
            dumpRecordPoints(verts, '.points_00A.obj', context)
            pass

    class Format_0B:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize >= 120)
            row.append(Key(bd))       # key - all .003?
            expectValue(row[-1].typeId, 0x003, "format 0x0B references {} instead .003".format(row[1]))
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat
            row.append(bd.readU32())  # extraCount
            extraCount = row[-1]
            assert(extraCount >= 0)
            if bd.tell() - recHeader.recordStartOffset != 76:
                print(bd.tell() - recHeader.recordStartOffset)
                print(tabulate([row]))
            assert((bd.tell() - recHeader.recordStartOffset) == 76)

            for i in range(0, 11):
                row.append(bd.readU32()) # unk

            for i in range(extraCount):
                row.append(bd.readU32()) # unk1
                row.append(bd.readU32()) # unk2
                
            pass

        @staticmethod
        def dump(tab, context):
            verts = [row[2] for row in tab]
            dumpRecordPoints(verts, '.points_00B.obj', context)
            pass

    class Format_0C:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 72)
            row.append(Key(bd))       # key - all .02c ?
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat

            expectValue(row[1].typeId, 0x02c, "format 0x0c references {} instead .02c".format(row[1]))
            pass

        @staticmethod
        def dump(tab, context):
            verts = [row[2] for row in tab]
            dumpRecordPoints(verts, '.points_00C.obj', context)
            pass

    class Format_0D:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 88)
            row.append(Key(bd))       # key - all .00d ?
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat
            for i in range(4):
                row.append(bd.readU32()) #
                expectValue(row[-1], 0, "format 0x0d has non-zero at the end")
            expectValue(row[1].typeId, 0x00d, "format 0x0d references {} instead .00d".format(row[1]))
            pass

        @staticmethod
        def dump(tab, context):
            verts = [row[2] for row in tab]
            dumpRecordPoints(verts, '.points_00D.obj', context)
            pass

    class Format_0E:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 136)
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat
            row.append(bd.read3F32()) # unk1 pos? bboxMax?
            for i in range(7): row.append(bd.readF32()) #unk2
            row.append(Key(bd)) # key - references .004 or .001? 
            for i in range(6): row.append(bd.readF32()) #unk3
            pass

        @staticmethod
        def dump(tab, context):
            verts = [row[1] for row in tab]
            dumpRecordPoints(verts, '.points_00E.obj', context)
            pass

    class Format_0F:
        @staticmethod
        def read(bd, row, recHeader):
            assert(recHeader.recordSize == 80)
            row.append(bd.read3F32()) # pos
            row.append(bd.read3F32()) # scl
            row.append(bd.read4F32()) # quat
            row.append(bd.read3F32()) # unk1? bboxMax?
            row.append(bd.readU32()) #unk2
            expectValue(row[-1], 0, "format 0x0f has non-zero unk1")
            pass

        @staticmethod
        def dump(tab, context):
            verts = [row[1] for row in tab]
            dumpRecordPoints(verts, '.points_00F.obj', context)
            pass

    formats = {}
    formats[0x1] = Format_01
    formats[0x2] = Format_02_08
    formats[0x3] = Format_03
    formats[0x4] = Format_04
    formats[0x7] = Format_07
    formats[0x8] = Format_02_08
    formats[0x9] = Format_09
    formats[0xA] = Format_0A
    formats[0xB] = Format_0B
    formats[0xC] = Format_0C
    formats[0xD] = Format_0D
    formats[0xE] = Format_0E
    formats[0xF] = Format_0F


    print('pos datatable = {:x}'.format(bd.tell()))

    tab = []
    maxColumnCount = 0
    for i in range(context.header.countRecords):
        row = []
        recHeader = CommonRecordHeader(bd)
        row.append(recHeader)

        rowEndOffset = recHeader.recordStartOffset + recHeader.recordSize

        assert(recHeader.recordSize >= (16+4+4)//4)

        lastDefCol = 6

        if recHeader.type in formats:
            formats[recHeader.type].read(bd, row, recHeader)
        else:
            Format_Unk.read(bd, row, recHeader)
        
        maxColumnCount = max(len(row), maxColumnCount)

        assert(bd.tell() <= rowEndOffset)
        assert(bd.tell() == rowEndOffset)
        if bd.tell() < rowEndOffset:
            bd.seekSet(rowEndOffset)

        tab.append(row)

    print('maxColumnCount =', maxColumnCount)
    headers = range(0, maxColumnCount)

    for r in tab:
        while len(r) < maxColumnCount:
            r.append('_')


    print(tabulate(tab, headers=headers, floatfmt='.6'))
    # print(tab)
    # for r in tab:
        # print(r)


    if recHeader.type in formats:
        formats[recHeader.type].dump(tab, context)

    pass


def readFile0BC(context):
    filedata = None
    with open(context.filepath, 'rb') as f:
        filedata = f.read()

    bd = BinData(filedata)
    print('file size =', bd.dataSize())

    h = readHeader0BC(bd)
    context.header = h
    pprint(h)

    if h.maybeDataType == 1:
        assert(context.expectedFormat == 0x10)
        # assert(h.countRecords == 0)
        readPhysicalCollision0BC(bd, context)
    elif h.maybeDataType != 0:
        print('Yet unknown and unexpected header')
        assert(False)
    else:
        if context.expectedFormat == 0x12:
            readRecords0BC_format_12(bd, context)
        else:
            readRecords0BC(bd, context)



    print(bd.tell(), bd.dataSize())

    # if bd.tell() < bd.dataSize():
        # print(bd.readHex(bd.dataSize() - bd.tell()))
        # pass

    # posCol = 8
    # posCol -= 3
    # verts = [row[posCol:(posCol+3)] for row in tab]
    # with open('verts5.obj', 'w') as f:
    #     obj_file.writeVertices(f, verts)







def prepExport0BC(filepath, exportPath):
    context = ProcessingContext()
    context.filename = filepath.name
    context.filepath = str(filepath)
    context.exportPath = exportPath
    context.expectedFormat = int(context.filename[0:4], 16)
    print('===================================')
    print(context.filename)
    readFile0BC(context)

def exportAll0BC(pathRoot):
    exportPath = pathRoot / 'exp'
    exportPath.mkdir(exist_ok=True)
    print('pathRoot =', pathRoot)
    for filepath in pathRoot.glob('*.0bc'):
        prepExport0BC(filepath, exportPath)

def listAndExtportAll():
    for p in Path('d:/ow/fl/').glob('*'):
        pathRoot = p / '0BC'
        exportAll0BC(pathRoot)

def exportSpecific0BC(filepath):
    exportPath = filepath.parent / 'exp'
    exportPath.mkdir(exist_ok=True)
    print('filepath =', filepath)
    prepExport0BC(filepath, exportPath)

# filepath = Path(r'd:/ow/fl/06111D3552663A20EF89AC14D4C9413C/0BC/000100000165.0BC')
# filepath = Path(r'd:/ow/fl/8B79091735A20C086C54C35FA6C51BB7/0BC/00100000066D.0BC')
# exportSpecific0BC(filepath)

pathRoot = Path(r'd:/ow/fl/1E6EE3845D0F77AD62EACC08C7D114FF/0BC/')
exportAll0BC(pathRoot)