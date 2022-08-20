#!/usr/bin/env python
# -*- coding: utf-8 -*-
#import requests
import xml.etree.ElementTree as ET
import json
import bpy
import math
from bpy_extras import object_utils
import numpy as np

class Verts:
    def __init__(self):
        self.vertex = []
        self.id = ""
class Object:
    def __init__(self):
        self.posList = []
class Result:
    def __init__(self):
        self.objects = []
        self.textures = {}


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
        W = np.sqrt(1-(self.E2*np.arcsin(avglat)))
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
        self.STRINGATRIB = "{http://www.opengis.net/citygml/generics/2.0}stringAttribute"
        self.dc = DistanceCalc()
    def searchPosList(self,data,posList):
        for child in data:
            #if child.tag == self.STRINGATRIB:
            #    if child.attrib["name"] == "建物ID":
            #        bldgid = child[0].text
            posList = self.searchPosList(child,posList)
            if child.tag == self.POSLIST:
                gmlid = "0"
                if self.GMLID in data.attrib:
                    gmlid = data.attrib[self.GMLID] 
                posList.append({"id":gmlid,"vertex":np.asfarray(child.text.split(" "),dtype=float)})
        return posList
    def CreateDict(self,data):
        gmlid = data.attrib[self.GMLID]
        posList = []
        posList = self.searchPosList(data,posList)
        return {"posList":posList,"id":gmlid}

    def CityObjectParse(self,data):
        for child in data:
            city = self.CreateDict(child)
        return city

    def TextureParse(self,data,result):
        coords = []
        for child in data:
            result.textures[child.attrib["ring"]] = np.asfarray(child.text.split(" "),dtype=float)
            pass
        return result

    def load(self,filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.parse(root)
    
    def parse(self,obj):
        temp = Result()
        return self._parse(obj,temp)

    def _parse(self,obj,result):
        for child in obj:
            if child.tag == "{http://www.opengis.net/citygml/2.0}cityObjectMember":
                o = self.CityObjectParse(child)
                result.objects.append(o)
            elif child.tag  == "{http://www.opengis.net/citygml/appearance/2.0}TexCoordList":
                uri = obj.attrib["uri"]
                if uri in result.textures :
                    print("aruyo")
                    print(uri)
                    #exit()
                result = self.TextureParse(child,result)
            else :
                result = self._parse(child,result)
        return result

    def positionSet(self,result,clat,clon,celev,context,scale):
        verts = []
        for obj in result.objects:
            verts = []
            faces = []
            vindex = 0
            for o2 in obj["posList"]:
                lid = "-"
                if o2["id"] != "0":
                    pass
                    lid = "#"+o2["id"]
                    if lid in result.textures:
                        pass
                indexes = []
                for i in range(0,len(o2["vertex"]),3):
                    lat = o2["vertex"][i]
                    lon = o2["vertex"][i+1] 
                    hig = o2["vertex"][i+2] 
                    (x,y) = self.dc.calc(lat,lon,clat,clon)
                    hig = hig - celev
                    verts.append([x*scale,y*scale,hig*scale])
                    indexes.append(vindex)
                    vindex += 1
                faces.append(indexes)
            n_mesh = bpy.data.meshes.new(obj["id"])
            n_mesh.from_pydata(verts,[],faces)
            n_mesh.update()
            object_utils.object_data_add(context, n_mesh, operator=None)
