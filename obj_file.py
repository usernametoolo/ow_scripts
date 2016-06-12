import math

def writeHeader(f):
    f.write('# OBJ file\n')

def writeVertices(f, verts):
    for v in verts:
        f.write('v {0} {1} {2}\n'.format(*v))


def writeLines(f, lineVerts):
    for v in lineVerts:
        f.write('v {0} {1} {2}\n'.format(*v))
    for i in range(0, len(lineVerts) // 2):
        f.write('l {0} {1}\n'.format(i*2 + 1, i*2 + 2))


def writeTrigs(f, trigVerts):
    for v in trigVerts:
        f.write('v {0} {1} {2}\n'.format(*v))
    for i in range(0, math.floor(len(trigVerts) // 3)):
        f.write('f {0} {1} {2}\n'.format(i*3 + 1, i*3 + 2, i*3 + 3))

def writeTrigIndices(f, trigIndices, offset = 1):
    for idx in trigIndices:
        f.write('f {0} {1} {2}\n'.format(idx[0] + offset, idx[1] + offset, idx[2] + offset))