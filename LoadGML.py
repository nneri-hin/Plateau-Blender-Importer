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

lodTypes = {
        "LOD0FP":0,
        "LOD0RE":0,
        "LOD1":1,
        "LOD2":2,
        "LODX":2
}
class Verts:
    def __init__(self,_id,vertex,lodType):
        self.vertex = vertex
        self.id = _id
        self.lod = lodTypes[lodType]
        self.lodType = lodType
class Object:
    def __init__(self,_id,posList,enableTexture,uri):
        self.id = _id
        self.posList = posList
        self.minLod = 10
        self.maxLod = 0
        for verts in posList:
            #if verts.lodType == "LOD0RE":
            #    #RoofEdgeだけの場合はLOD0は無視する。FootPrintがあればそっちを使う
            #    continue
            if self.maxLod < verts.lod :
                self.maxLod = verts.lod
            if self.minLod > verts.lod :
                self.minLod = verts.lod
            pass
        self.enableTexture = enableTexture
        self.uri = uri
        self.boundingBox = np.array([90,180,-90,-180,0,0],dtype=np.float64)
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
        self.BOUNDED     = "{http://www.opengis.net/citygml/building/2.0}boundedBy"

        self.LOD0FP      = "{http://www.opengis.net/citygml/building/2.0}lod0FootPrint"
        self.LOD0RE      = "{http://www.opengis.net/citygml/building/2.0}lod0RoofEdge"
        self.LOD1        = "{http://www.opengis.net/citygml/building/2.0}lod1Solid"
        self.LOD2        = "{http://www.opengis.net/citygml/building/2.0}lod2Solid"

        self.dc = DistanceCalc()
    def searchPosList(self,data,posList,enableTexture,uri,lod):
        for child in data:
            if child.tag == self.LOD0FP:
                lod = "LOD0FP"
            if child.tag == self.LOD0RE:
                lod = "LOD0RE"
            if child.tag == self.LOD1:
                lod = "LOD1"
            if child.tag == self.LOD2:
                lod = "LOD2"
            (posList,enableTexture,uri,lod) = self.searchPosList(child,posList,enableTexture,uri,lod)

            if child.tag == self.POSLIST:
                gmlid = "0"
                if self.GMLID in data.attrib:
                    gmlid = data.attrib[self.GMLID] 
                    enableTexture = True
                #posList.append({"id":gmlid,"vertex":np.asfarray(child.text.split(" "),dtype=float)})
                posList.append(Verts(gmlid, np.asfarray(child.text.split(" "),dtype=np.float64),lod ) )
        return (posList,enableTexture,uri,lod)

    def CreateDict(self,data):
        gmlid = data.attrib[self.GMLID]
        posList = []
        (posList,enableTexture,uri,lod)= self.searchPosList(data,posList,False,"","LODX")
        #for i in posList:
        #    print(gmlid,i.lod)
        #return {"posList":posList,"id":gmlid,"enableTexture":enableTexture,"uri":uri}
        return Object(gmlid,posList,enableTexture,uri)

    def CityObjectParse(self,data):
        maxPos = [-90,-180] 
        minPos = [90,180]
        for child in data:
            city = self.CreateDict(child)
            for p in city.posList:
                city.boundingBox[0] = np.min(np.append(p.vertex[::3] , city.boundingBox[0]) )
                city.boundingBox[1] = np.min(np.append(p.vertex[1::3] , city.boundingBox[1]) )
                city.boundingBox[2] = np.max(np.append(p.vertex[::3] , city.boundingBox[2]) )
                city.boundingBox[3] = np.max(np.append(p.vertex[1::3] , city.boundingBox[3]) )
            city.boundingBox[4] = (city.boundingBox[0]+city.boundingBox[2])/2
            city.boundingBox[5] = (city.boundingBox[1]+city.boundingBox[3])/2
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

    def _parse(self,obj,result,texture,depth):
        children = []
        for child in obj:
            if child.tag == self.CITYOBJECT:
                o = self.CityObjectParse(child)
                result.objects.append(o)
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

    def positionSet(self,result,clat,clon,celev,scale,viewRange):
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
            dist = self.dc.calc(clat,clon,obj.boundingBox[4],obj.boundingBox[5])
            if viewRange > 0  and  ( np.abs(dist[0]) > viewRange or np.abs(dist[1])  > viewRange ) : 
                continue
            #print(obj["id"],obj["enableTexture"])
            for o2 in obj.posList:#osはposList
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
                lodSplit = [[],[],[]]#lod0~2
                for i in range(0,len(o2.vertex),3):
                    lat = o2.vertex[i]
                    lon = o2.vertex[i+1] 
                    hig = o2.vertex[i+2] 
                    key = str(lat)+","+str(lon)+","+str(hig)
                    if o2.lod != obj.maxLod:
                        continue
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
