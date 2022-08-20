bl_info = {
    "name": "Import Plateau CityGML",
    "author": "Hin(@thamurian)",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    #"support":"TESTING",
    "category": "Import-Export",
    "description": "Import geometry from CityGML file(s).",
    "wiki_url": "https://github.com/nneri-hin/Plateau-Blender-Importer",    
}

import os
#from xml.etree import ElementTree as et
import bpy
from bpy_extras.io_utils import ImportHelper
import re
from bpy.props import (BoolProperty,
                       FloatProperty,
                       IntProperty,
                       StringProperty,
                       EnumProperty,
                       CollectionProperty,
                       FloatVectorProperty)
from . import LoadGML
#if "bpy" in locals():
#    print("imp")
#    import imp
#    imp.reload(LoadGML)
#

class PlateauImporter(bpy.types.Operator, ImportHelper):

    bl_idname = "hin.plateau_importer"
    bl_label = "pick an gml file(s)"
    filename_ext = ".gml"
    use_filter_folder = True
    files: CollectionProperty(type=bpy.types.PropertyGroup)
    origin_setting_jmc: StringProperty(
        name="Origin Japan Mesh Code",
        description="Origin Japan Mesh Code",
        default="53394611"
        )
    scale: FloatProperty(
        name="Scale",
        description="Scale object size",
        default=1.0
        )

    def execute(self,context):
        pass
        folder = (os.path.dirname(self.filepath))
        loader = LoadGML.LoadGML()
        meshcode = "53394611"
        if len(self.origin_setting_jmc) ==  8  and re.search("\D",self.origin_setting_jmc):
            print("Wrong meshcode")
        else:
            meshcode = self.origin_setting_jmc
        jmTool = JapanMeshTool()
        clat,clon = jmTool.getCenter(meshcode)
        for i in self.files:
            path_to_file = (os.path.join(folder, i.name))
            result = loader.load(path_to_file)
            loader.positionSet(result,clat,clon,0,context,self.scale)

        return {'FINISHED'}
def menu_import(self, context):
    self.layout.operator(PlateauImporter.bl_idname, text="Plateau cityGML (.gml)")

def register():
    bpy.utils.register_class(PlateauImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.utils.unregister_class(PlateauImporter)


##こっからC#のコピペ改造
class JapanMeshTool:
    #三次メッシュしか対応してません
    def getNeighbor(self,meshcode,lat ,lon):
        #隣接メッシュを取得します
        lat1 = meshcode[0:2]
        lon1 = meshcode[2:4]
        lat2 = meshcode[4:5]
        lon2 = meshcode[5:6]
        lat3 = meshcode[6:7]
        lon3 = meshcode[7:8]
        tlat = str(int(lat1 + lat2 + lat3) + lat).zfill(4)
        tlon = str(int(lon1 + lon2 + lon3) + lon).zfill(4)
        return tlat[0:2]+ tlon[0:2] + tlat[2:3] + tlon[2:3] + tlat[3:4] + tlon[3:4]
    def toMeshCode(self,lat ,lon):
        #メッシュコードは3次メッシュ固定です
        #緯度の計算
        p = np.floor(lat * 1.5)
        a = (lat * 60) % 40
        q = np.floor(a / 5)
        b = a % 5
        r = np.floor(b * 60 / 30)
        u = np.floor(lon - 100)
        f = lon - u - 100
        v = np.floor(f * 60 / 7.5)
        g = f * 60 % 7.5
        w = np.floor(g * 60 / 45)
        return str(p)+str(u)+str(q)+str(v)+ str(r) + str(w)
    def toLatLon(self,meshcode):
        lat1 =  float(meshcode[0: 2]) / 60 * 40
        lon1 =  float(meshcode[2: 4]) + 100
        lat2 = (float(meshcode[4: 5]) * 2/3)/8 
        lon2 =  float(meshcode[5: 6]) /8
        lat3 =  float(meshcode[6: 7]) * (2/3) / 80
        lon3 =  float(meshcode[7: 8]) / 80
        latlon = [ lat1 + lat2 + lat3, lon1 + lon2 + lon3 ]
        return latlon
    def getCenter(self,meshcode):
        latlon1 = self.toLatLon(meshcode)
        latlon2 = self.toLatLon(self.getNeighbor(meshcode, 1, 1))
        #return new float[2] { (latlon1[0] + latlon2[0]) / 2, (latlon1[1] + latlon2[1]) / 2 }
        return [ (latlon1[0] + latlon2[0]) / 2 ,(latlon1[1] + latlon2[1]) /2]

