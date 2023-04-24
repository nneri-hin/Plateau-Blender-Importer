#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import requests
import bpy
import bmesh
import math
from bpy_extras import object_utils
import numpy as np
import os

class Textures:
    def __init__(self):
        self.textures = []
        self.cnt = 0
        pass
    def add(self,texture):
        if texture not in self.textures:
            self.textures.append(texture)
        return self.textures.index(texture)
        


class SetMesh:
    def __init__(self):
        pass
    def create_material(self,directory,texture,emission):
        path_to_file = (os.path.join(directory, texture))
        image = bpy.data.images.load(path_to_file)
        mat = bpy.data.materials.new(texture)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        tex = nodes.new(type='ShaderNodeTexImage')
        tex.location = (-300,300)
        tex.image = image
        bsdf = None
        #ShaderNodeBsdfPrinciple
        #ShaderNodeEmission
        output = None
        em = None
        if emission :
            em = nodes.new("ShaderNodeEmission")
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf =  node
            if node.type == "OUTPUT_MATERIAL":
                output = node
        #bsdf = nodes['Principled BSDF']
        if bsdf is not None:
            if emission:
                mat.node_tree.links.new(tex.outputs[0],em.inputs[0])
                mat.node_tree.links.new(em.outputs[0],output.inputs[0])
                nodes.remove(bsdf)
            else:
                mat.node_tree.links.new(tex.outputs[0],bsdf.inputs[0])
        return mat
    def create_blank_material(selfa,emission):
        mat = bpy.data.materials.new("Default")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        if emission :
            em = nodes.new("ShaderNodeEmission")
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf =  node
            if node.type == "OUTPUT_MATERIAL":
                output = node
        if bsdf is not None:
            if emission:
                mat.node_tree.links.new(em.outputs[0],output.inputs[0])
                nodes.remove(bsdf)
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
        textures = Textures()
        for face in bm.faces:
            #for loop in face.loops:
            for i in range(len(face.loops)):
                if len(uvmap[cnt]["uv"]) > i* 2:
                    face.loops[i][uv].uv = [uvmap[cnt]["uv"][i*2],uvmap[cnt]["uv"][i*2+1]]
                    if uvmap[cnt]["texture"] != "":
                        texture = uvmap[cnt]["texture"]
                        face.material_index =  textures.add(uvmap[cnt]["texture"])
            cnt += 1
        bm.to_mesh(n_mesh)
        n_mesh.update()
        return textures.textures
    def mesh(self,context,poly,directory,name,import_texture,shader_type):
        materials = {}
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        blank = self.create_blank_material(shader_type == "AllEmission")
        for texture in poly["textures"]:
            materials[texture] = self.create_material(directory,texture,shader_type !=  "PrincipledBSDF")
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
            if obj.enableTexture and import_texture :
                textures = self.set_uvmap(n_mesh,uvmap)
                #この辺多分そのうちかえる
                #if texture != "":
                if len(textures) != 0:
                    for i in range(len(textures)):
                        texture = textures[i]
                        bObject.data.materials.append(materials[texture])
                    #bObject.active_material = materials[texture]
                    pass
                else :
                    bObject.active_material =  blank
            else :
                bObject.active_material =  blank
            collection.objects.link(bObject)
