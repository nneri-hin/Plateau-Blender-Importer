#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import requests
import bpy
import bmesh
import math
from bpy_extras import object_utils
import numpy as np
import os


class SetMesh:
    def __init__(self):
        pass
    def create_material(self,directory,texture):
        path_to_file = (os.path.join(directory, texture))
        image = bpy.data.images.load(path_to_file)
        mat = bpy.data.materials.new(texture)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        tex = nodes.new(type='ShaderNodeTexImage')
        tex.location = (-300,300)
        tex.image = image

        bsdf = nodes['Principled BSDF']
        mat.node_tree.links.new(tex.outputs[0],bsdf.inputs[0])
        return mat
    def create_blank_material(self):
        mat = bpy.data.materials.new("Default")
        mat.use_nodes = True
        return mat
        pass
        
    def set_uvmap(self,n_mesh,uvmap):
        #UVMapがあった場合面に設定する
        bm = bmesh.new()
        bm.from_mesh(n_mesh)
        uv = bm.loops.layers.uv.new("UVMap")
        cnt = 0
        texture = ""
        for face in bm.faces:
            #for loop in face.loops:
            for i in range(len(face.loops)):
                if len(uvmap[cnt]["uv"]) > i* 2:
                    face.loops[i][uv].uv = [uvmap[cnt]["uv"][i*2],uvmap[cnt]["uv"][i*2+1]]
                    if uvmap[cnt]["texture"] != "":
                        texture = uvmap[cnt]["texture"]
            cnt += 1
        bm.to_mesh(n_mesh)
        n_mesh.update()
        return texture
    def mesh(self,context,poly,directory,name):
        materials = {}
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        blank = self.create_blank_material()
        for texture in poly["textures"]:
            materials[texture] = self.create_material(directory,texture)
        for data in poly["datas"]:
            obj      = data["obj"]
            verts    = data["verts"]
            faces    = data["faces"]
            uvmap    = data["uvmap"]
            #textures = data["textures"]
            n_mesh = bpy.data.meshes.new(obj.id)
            n_mesh.from_pydata(verts,[],faces)
            n_mesh.update()
            #bObject = object_utils.object_data_add(context, n_mesh, operator=None)
            bObject = bpy.data.objects.new(obj.id,n_mesh)
            if obj.enableTexture :
                texture = self.set_uvmap(n_mesh,uvmap)
                #この辺多分そのうちかえる
                if texture != "":
                    bObject.active_material = materials[texture]
                else :
                    bObject.active_material =  blank
            else :
                bObject.active_material =  blank
            collection.objects.link(bObject)
