bl_info = {
    "name": "Import Plateau CityGML",
    "author": "Hin(@thamurian)",
    "version": (0, 9, 5),
    "blender": (3, 0, 0),
    #"support":"TESTING",
    "location":"File > Import-Export",
    "category": "Import-Export",
    "description": "Import geometry from CityGML file(s).",
    "wiki_url": "https://github.com/nneri-hin/Plateau-Blender-Importer",    
}

import os
import numpy as np
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
from . import SetMesh
#if "bpy" in locals():
#    print("imp")
#    import imp
#    imp.reload(LoadGML)
#

def get_shader_enum(scene,context):
    items = [
            ("PrincipledBSDF" ,"PrincipledBSDF" ,"PrincipledBSDF"        ,"PrincipledBSDF",0),
            ("TextureEmission","TextureEmission","Emission(TextureOnly)","TextureEmission",1),
            ("AllEmission"    ,"AllEmission"    ,"Emission(AllMaterial)" ,"AllEmission",2)
            ]
    return items

class PlateauImporter(bpy.types.Operator, ImportHelper):
    bl_idname = "hin.plateau_importer"
    bl_label = "pick an gml file(s)"
    filename_ext = ".gml"
    use_filter_folder = True
    files: CollectionProperty(type=bpy.types.PropertyGroup)
    origin_setting_jmc: StringProperty(
        name="Origin Japan Mesh Code Or Latlon ",
        description="Origin Japan Mesh Code Or Latlon(Ex.35.680, 139.766)",
        default="53394611"
        )
    scale: FloatProperty(
        name="Scale",
        description="Scale object size",
        default=1.0
        )
    range: FloatProperty(
        name="Range",
        description="Effective distance(km). If a negative value is entered, it is assumed to be infinite.",
        default=-1
        )
    limit_type: BoolProperty(
            name="Range limit vertex units",
            description="Delete out-of-range as vertex units",
            default=False
        )
    import_texture:BoolProperty(
            name="Import Texture",
            description="Import Textuure",
            default=True
        )
    shader_type:EnumProperty(
            name = "Shader Type",
            description = "select shader type. princpled bsdf of emission",
            #default="PrincipledBSDF",
            items = get_shader_enum
        )

    def execute(self,context):
        pass
        directory= (os.path.dirname(self.filepath))
        loader = LoadGML.LoadGML()
        setmesh = SetMesh.SetMesh()
        meshcode = "53394611"
        clat,clon = 0,0
        isMeshCode = True
        if re.search(',',self.origin_setting_jmc) :
            #Center is Latlon
            slat,slon = self.origin_setting_jmc.split(",")
            isMeshCode = False
            try:
                clat = float(slat)
                clon = float(slon)
            except:
                print("ParseError")
                isMeshCode = True
                pass
        if isMeshCode:
            if len(self.origin_setting_jmc) !=  8  or re.search("\D",self.origin_setting_jmc):
                print("Wrong meshcode")
            else:
                meshcode = self.origin_setting_jmc
            print(meshcode)
            jmTool = LoadGML.JapanMeshTool()
            clat,clon = jmTool.getCenter(meshcode)
        for i in self.files:
            path_to_file = (os.path.join(directory, i.name))
            result = loader.load(path_to_file)
            poly = loader.positionSet(result,clat,clon,0,self.scale,self.range * 500,self.limit_type)
            print(self.shader_type)
            setmesh.mesh(context,poly,directory,i.name,self.import_texture,self.shader_type)

        return {'FINISHED'}
def menu_import(self, context):
    self.layout.operator(PlateauImporter.bl_idname, text="Plateau cityGML (.gml)")

def register():
    bpy.utils.register_class(PlateauImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.utils.unregister_class(PlateauImporter)



