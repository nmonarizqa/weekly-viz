'''
Extracting Results from Here Maps routing API for Jakarta
Author: Nurvirta Monarizqa
Date: November 26, 2017
Required: jadetabek_desa.geojson

Inputs: app_code, app_id, time, filename output
format time: %Y-%m-%dT%H:%M:%S

This script will pass time as departure time by default
and Senayan as destination. Feel free to modify.
'''

import pandas as pd
import geopandas as gpd
import numpy as np
import json
import urllib2
import sys
import osmnx as ox

def get_url(start_point,end_point,dep_hour=None,arr_hour=None,mode='car',app_code, app_id):
    base='https://route.cit.api.here.com/routing/7.2/calculateroute.json?app_id='+app_id+'&app_code='+app_code
    start='&waypoint0='+str(start_point.y)+","+str(start_point.x)
    end='&waypoint1='+str(end_point.y)+","+str(end_point.x)
    if mode=='car':
        params='&mode=fastest;car;traffic:enabled&maneuverAttributes=sh'
        departure='&departure='+dep_hour
        url = base+start+end+params+departure
    else:
        params='&combineChange=true&mode=fastest;publicTransportTimeTable&maneuverAttributes=sh'
        arrival='&arrival='+arr_hour
        url = base+start+end+params+arrival
    return url   

def get_result(data):
    distance = []
    travel_time = []
    shapes = []
    legs = data["response"]["route"][0]["leg"]
    for leg in legs:
        distance.append(leg["length"])
        travel_time.append(leg["travelTime"])
        for sh in leg["maneuver"]:
            shapes += sh["shape"]
    ln=ox.LineString(map(lambda x: (float(x.split(",")[1]),float(x.split(",")[0])), shapes))
    gdf=gpd.GeoDataFrame({'distance':distance,'time':travel_time,'geometry':[ln]})
    return gdf 

def get_df(start,end,time,mode='car',app_code,app_id):
    url = get_url(start,end,dep_hour=time,mode=mode,app_code,app_id)
    response=urllib2.urlopen(url)
    data = json.load(response)
    gdf = get_result(data)
    return gdf

if __name__ == "main":
  app_code = sys.argv[1]
  app_id = sys.argv[2]
  tm = sys.argv[3]
  fname = sys.argv[4]

  desa = gpd.GeoDataFrame.from_file("jadetabek_desa.geojson")
  center = desa.centroid
  all_result = gpd.GeoDataFrame()
  for i in range(len(desa)):
      gdf = get_df(center[i],center[202],tm,mode='car',app_code,app_id)
      gdf['KECAMATAN'] = desa.iloc[i].KECAMATAN
      gdf['KELURAHAN'] = desa.iloc[i].KELURAHAN
      all_result = pd.concat([all_result,gdf])
      print '\r','%',str(i*100./len(desa))[:5],
  all_result.to_file(driver='GeoJSON',filename=fname)
  print "Done exporting for " + fname

