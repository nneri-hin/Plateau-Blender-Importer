#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import requests
import xml.etree.ElementTree as ET
import json
#import bpy
#import bmesh
import math
#from bpy_extras import object_utils
import numpy as np
import os 

class Verts:
    def __init__(self,_id,vertex):
        self.vertex = vertex
        self.id = _id
class Object:
    def __init__(self,_id,posList,enableTexture,uri):
        self.id = _id
        self.posList = posList
        self.enableTexture = enableTexture
        self.uri = uri
class ParseResult:
    def __init__(self):
        self.objects = []
        self.uvmap = {}
        self.textures = set()



class DistanceCalc:
    def __init__(self):
        #WGS84
        self.a = 6378137 #長半径
        self.b = 6356752.314245 #短半径 
        self.f = 1 / 298.257223563 #扁平率
        self.E = 0.081819191042815790
        self.E2 = 0.006694380022900788
        #Φ1 = 緯度 L1 経度 （出発)
        pass
    def calc(self,lat1,lon1,lat2,lon2):
        #ヒュベニの公式を使用している
        radlat1 = np.radians(lat1)
        radlon1 = np.radians(lon1)
        radlat2 = np.radians(lat2)
        radlon2 = np.radians(lon2)
        avglat = (radlat1 + radlat2)/2
        dy = radlat1 - radlat2
        dx = radlon1 - radlon2
        #W = np.sqrt(1-(self.E2*np.arcsin(avglat)))
        W = np.sqrt(1-(self.E2 * np.power(np.sin(avglat),2) ))
        M =  (self.a*(1-self.E2))/np.power(W,3)
        N = self.a / W
        x = dx * N * np.cos(avglat)
        y = dy  * M
        #本来は下の公式で距離を出すが、今回はx,yが必要なのでそのまま返す
        #return (x,y,np.sqrt(np.power(x,2)+np.power(y,2)))
        return x,y
        

class LoadGML:
    def __init__(self):
        pass
        self.POSLIST     = "{http://www.opengis.net/gml}posList"
        self.GMLID       = "{http://www.opengis.net/gml}id"
        self.IMAGEURI    = "{http://www.opengis.net/citygml/appearance/2.0}imageURI"
        self.STRINGATRIB = "{http://www.opengis.net/citygml/generics/2.0}stringAttribute"
        self.CITYOBJECT  = "{http://www.opengis.net/citygml/2.0}cityObjectMember"
        self.TEXCOORD    = "{http://www.opengis.net/citygml/appearance/2.0}TexCoordList"
        self.dc = DistanceCalc()
    def searchPosList(self,data,posList,enableTexture,uri):
        for child in data:
            #if child.tag == self.STRINGATRIB:
            #    if child.attrib["name"] == "建物ID":
            #        bldgid = child[0].text
            (posList,enableTexture,uri) = self.searchPosList(child,posList,enableTexture,uri)
            if child.tag == self.POSLIST:
                gmlid = "0"
                if self.GMLID in data.attrib:
                    gmlid = data.attrib[self.GMLID] 
                    enableTexture = True
                #posList.append({"id":gmlid,"vertex":np.asfarray(child.text.split(" "),dtype=float)})
                posList.append(Verts(gmlid, np.asfarray(child.text.split(" "),dtype=float) ) )
        return (posList,enableTexture,uri)
    def CreateDict(self,data):
        gmlid = data.attrib[self.GMLID]
        posList = []
        (posList,enableTexture,uri)= self.searchPosList(data,posList,False,"")
        #return {"posList":posList,"id":gmlid,"enableTexture":enableTexture,"uri":uri}
        return Object(gmlid,posList,enableTexture,uri)

    def CityObjectParse(self,data):
        for child in data:
            city = self.CreateDict(child)
        return city

    def UVParse(self,data,result,texture):
        coords = []
        for child in data:
            result.uvmap[child.attrib["ring"]] ={"texture":texture,"uv": np.asfarray(child.text.split(" "),dtype=float)}
            pass
        return result

    def load(self,filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.parse(root)
    
    def parse(self,obj):
        temp = ParseResult()
        return self._parse(obj,temp,"",0)

        print(str(depth)+"-----")
    def _parse(self,obj,result,texture,depth):
        children = []
        for child in obj:
            #if child.tag == "{http://www.opengis.net/citygml/2.0}cityObjectMember":
            if child.tag == self.CITYOBJECT:
                o = self.CityObjectParse(child)
                result.objects.append(o)
            #elif child.tag  == "{http://www.opengis.net/citygml/appearance/2.0}TexCoordList":
            elif child.tag == self.TEXCOORD:
                result = self.UVParse(child,result,texture)
                #print(str(depth)+":TEXCOORD")
            elif child.tag == self.IMAGEURI:
                texture = child.text
                result.textures.add(child.text)
            else :
                children.append(child)
        #下に降りるときは一度その層を全部見てからにする
        for child in children:
            result = self._parse(child,result,texture,depth+1)
        return result

    #def set_uvmap(self,n_mesh,uvmap):
    #    #UVMapがあった場合面に設定する
    #    bm = bmesh.new()
    #    bm.from_mesh(n_mesh)
    #    uv = bm.loops.layers.uv.new("UVMap")
    #    cnt = 0
    #    for face in bm.faces:
    #        #for loop in face.loops:
    #        for i in range(len(face.loops)):
    #            if len(uvmap[cnt]) > i* 2:
    #                face.loops[i][uv].uv = [uvmap[cnt][i*2],uvmap[cnt][i*2+1]]
    #        cnt += 1
    #    bm.to_mesh(n_mesh)
    #    n_mesh.update()
    def positionSet(self,result,clat,clon,celev,scale):
        #tets用53393641
        verts = []
        datas = []
        for obj in result.objects:
            verts = []
            vertsMerge={}
            faces = []
            faces_tex = []
            vindex = 0
            uvmap = []
            #print(obj["id"],obj["enableTexture"])
            for o2 in obj.posList:
                lid = "-"
                if obj.enableTexture and o2.id == "0":
                    #テクスチャ有効時、idが0のものはスキップする
                    continue
                if obj.enableTexture:
                    lid = "#"+o2.id
                    if lid in result.uvmap:
                        uvmap.append(result.uvmap[lid])
                    else:
                        uvmap.append({"uv":[0.4,0.4],"texture":""})
                #else:
                #    uvmap.append([])
                indexes = []
                for i in range(0,len(o2.vertex),3):
                    lat = o2.vertex[i]
                    lon = o2.vertex[i+1] 
                    hig = o2.vertex[i+2] 
                    key = str(lat)+","+str(lon)+","+str(hig)
                    if key in vertsMerge:
                        indexes.append(vertsMerge[key])
                    else:
                        vertsMerge[key] = vindex
                        indexes.append(vindex)
                        (x,y) = self.dc.calc(lat,lon,clat,clon)
                        hig = hig - celev
                        verts.append([x*scale,y*scale,hig*scale])
                        vindex += 1
                if len(indexes) > 0 :
                    faces.append(indexes)
            datas.append({ "obj":obj,"verts":verts,"faces":faces,"uvmap":uvmap })
        return {"datas":datas,"textures":result.textures}
    def get_image_path(self,filename,texture):
        dir = os.path.dirname(filename)
        path = dir + texture
        print(path)

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
if __name__ == "__main__":
    pass
