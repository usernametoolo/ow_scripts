import pickle
from pathlib import Path

# import bpy

import mathutils
from bpy_extras.io_utils import axis_conversion

import importlib
import types_0bc
importlib.reload(types_0bc)

from types_0bc import Key, CommonRecordHeader




def deleteAllObjects():
    objects = [item for item in bpy.data.objects if item.type == "MESH"]

    for obj in objects:
        for sc in tuple(obj.users_scene):
            sc.objects.unlink(obj)

    for obj in objects:
        #obj.select = True
        bpy.data.objects.remove(obj)

    # select them only.
    # for object_name in candidate_list:
      # bpy.data.objects[object_name].select = True

    # remove all selected.
    # bpy.ops.object.delete()


def unlinkObjectsFromScene(scene):
    objects = [obj for obj in scene.objects]

    for obj in objects:
        scene.objects.unlink(obj)

def deleteUnusedObjects():
    for o in [ob for ob in bpy.data.objects if ob.users == 0]:
        bpy.data.objects.remove(o)

def deleteUnusedMeshes():
    for mesh in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(mesh)

def selectScene(scene):
    bpy.context.screen.scene = scene
    return scene

def createScene(sceneName):
    if sceneName in bpy.data.scenes:
        print('removing scene ', sceneName)
        bpy.data.scenes.remove(bpy.data.scenes[sceneName])

    print('createScene ', sceneName)
    return bpy.data.scenes.new(sceneName)

def selectSceneByName(sceneName):
    return selectScene(bpy.data.scenes[sceneName])
    

def importModelObjIntoScene_asdfadf(filePath):
    # try:
        # bpy.ops.import_scene.obj(filepath=filePath, use_split_groups=False)
    # except FileNotFoundError as err:
        # print('unable to import obj: ', err)
    if Path(filePath).exists():
        print('exists!')
        bpy.ops.import_scene.obj(filepath=filePath, use_split_groups=False)
    else:
        print('path doesnt exist: ', filePath)

def importModelObj(modelName, modelPath):
    print('importModelObj_asdasdf ', modelName, ' - ', modelPath)
    sceneName = 'model/' + modelName
    scene = createScene(sceneName)
    selectScene(scene)
    importModelObjIntoScene_asdfadf(modelPath)
    if len(scene.objects) == 0:
        print('nothing was loaded!')
        return
    if len(scene.objects) > 1:
        print('more that 1 object was loaded!')
    scene.objects[0].name = modelName


def loadModelByKey(modelKey, context):
    modelPath = context.exportedModelsPath / (str(modelKey) + '.obj')
    print(modelPath)

    importModelObj(str(modelKey), str(modelPath))


def loadUsedModels_Format01(tab, context):
    # modelKey = '00000000078c.00c'
    # loadModelByKey(modelKey, exportedModelsPath)

    for objRecord in tab:
        modelKey = objRecord[1]
        loadModelByKey(modelKey, context)


def convertPos(pos, context):
    vec = mathutils.Vector(pos[0:3])
    return vec * context.axis_conversion_matrix
    # return (pos[0], pos[1], pos[2])

def convertScl(scl, context):
    # vec = mathutils.Vector(scl[0:3])
    # return vec * context.axis_conversion_matrix
    return (scl[0], scl[1], scl[2])
    # return (scl[0], scl[2], scl[1])

def convertRot(rot, context):
    quat = mathutils.Quaternion((rot[3], rot[0], rot[1], rot[2]))
    quat.rotate(context.axis_conversion_matrix)
    return quat
    # return (rot[3], rot[0], rot[1], rot[2])

    # quat = mathutils.Quaternion((rot[3], *convertPos(rot[0:3], context)))
    # return quat

def getReferenceObjectMesh(modelKey, context):
    referenceObjects = context.referenceObjects
    refObjMesh = None
    if modelKey in referenceObjects:
        refObj = referenceObjects[modelKey]
        refObjMesh = refObj.data
        if not refObjMesh:
            print('getReferenceObjectMesh: model without mesh:', modelKey)
    else:
        print('getReferenceObjectMesh: unable to find model:', modelKey)
    return refObjMesh

def placeObject(objectName, modelMesh, pos, scl, rot, context):
    print(objectName, modelMesh, pos, scl, rot)

    obj = bpy.data.objects.new(objectName, modelMesh)

    # obj.matrix_world = context.axis_conversion_matrix

    # obj.location = convertPos(pos, context)
    # obj.rotation_mode = 'QUATERNION'
    # obj.rotation_quaternion = convertRot(rot, context)

    # bpy.context.scene.update()

    # print(obj.matrix_world)

    # obj.matrix_world = context.axis_conversion_matrix


    posMtx = mathutils.Matrix.Translation(pos)
    rotMtx = mathutils.Quaternion((rot[3], rot[0], rot[1], rot[2])).to_matrix().to_4x4()
    # print(posMtx)
    # print(rotMtx)

    xformMtx = posMtx * rotMtx
    # print(xformMtx)
    xformMtx = context.axis_conversion_matrix * xformMtx
    # print(xformMtx)
    obj.matrix_world = xformMtx


    obj.scale = convertScl(scl, context)

    return obj


def placeObjects_Format01(tab, context):

    modelWhiteList = set(['000000000dd5.00c'])

    modelsSkipList = set(['000000000d14.00c', 
        '000000000ac0.00c', 
        '000000000d47.00c',
        '000000000f13.00c'])


    scene = bpy.context.scene
    recordIdx = 0
    for record in tab:
        modelKey = str(record[1])

        # if modelKey in modelsSkipList:
            # continue
        # if modelKey not in modelWhiteList:
            # continue

        refObjMesh = getReferenceObjectMesh(modelKey, context)

        for group in record[7]:
            mtlKey = str(group[0])
            idx = 0
            for obj in group[3]:
                objectName = '{0}_{1}_{2}'.format(modelKey, mtlKey, idx)
                pos = obj[0]
                scl = obj[1]
                rot = obj[2]
                blenderObj = placeObject(objectName, refObjMesh, pos, scl, rot, context)
                scene.objects.link(blenderObj)
                idx += 1
        recordIdx += 1
        # if recordIdx == 5:
            # break

        
def listReferenceObjects(tab, context):
    referenceObjects = {}
    for objRecord in tab:
        modelKey = str(objRecord[1])

        if modelKey in bpy.data.objects:
            referenceObjects[modelKey] = bpy.data.objects[modelKey]

    # print(referenceObjects)
    context.referenceObjects = referenceObjects
    return
        

class ProcessingContext:
    def __init__(self, rootPath):
        self.levelRootPath = Path(rootPath)
        self.exportedModelsPath = self.levelRootPath / r'00C/exp'
        self.referenceObjects = {}
        self.axis_conversion_matrix = axis_conversion(from_forward='-Z', from_up='Y').to_4x4()
        # self.axis_conversion_matrix = mathutils.Matrix()


def main():
    context = ProcessingContext(r'd:/ow/fl/06111D3552663A20EF89AC14D4C9413C/')

    pickledMap = context.levelRootPath / r'0BC/exp/000100000165.0BC.data_001.pickle'

    with pickledMap.open(mode='rb') as f:
        tab = pickle.load(f)


    # deleteAllObjects()
    # deleteUnusedMeshes()
    # loadUsedModels_Format01(tab, context)

    scene = selectSceneByName('level')
    unlinkObjectsFromScene(scene)
    deleteUnusedObjects()
    deleteUnusedMeshes()

    listReferenceObjects(tab, context)
    placeObjects_Format01(tab, context)
    bpy.context.scene.update()

# main()