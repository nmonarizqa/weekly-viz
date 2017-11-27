'''
Extracting Results from Google Maps Routing API Transit for Jakarta
Author: Nurvirta Monarizqa
Date: November 26, 2017
Required: jadetabek_desa.geojson

Inputs: key, time, filename output
Time has to be in epoch.

This script will pass time as departure time by default
and Senayan as origin. Feel free to modify.
'''

import pandas as pd
import geopandas as gpd
import numpy as np
import json
import urllib2
import sys

def get_url(start_point,end_point,dep_time=None,arr_time=None):
    base='https://maps.googleapis.com/maps/api/directions/json?&key='+key
    start='&origin='+str(start_point.y)+","+str(start_point.x)
    end='&destination='+str(end_point.y)+","+str(end_point.x)
    params='&mode=transit'
    if dep_time != None:
        time = '&departure_time='+str(dep_time)
    if arr_time != None:
        time = '&arrival_time='+str(arr_time)
    url = base+start+end+params+time
    return url

def get_df(start,end, arr_time=None, dep_time=None):
    url=get_url(start_point=start,end_point=end,arr_time=arr_time,dep_time=dep_time)
    response=urllib2.urlopen(url)
    data = json.load(response)
    status  = data['status']
    try:
        mode = data['routes'][0]['legs'][0]['steps'][0]['travel_mode']
    except:
        mode=status
    try:
        travel_time = data['routes'][0]['legs'][0]['duration']['value']/60.
    except:
        travel_time=None
    try:
        dep_time=data['routes'][0]['legs'][0]['departure_time']['text']
    except:
        dep_time=None
    df = pd.DataFrame({'mode':[mode],'durasi':[travel_time],'berangkat':[dep_time],
                   'kelurahan':row_desa.KELURAHAN,'kecamatan':row_desa.KECAMATAN})
    return df

if __name__ == "main":
  key = sys.argv[1]
  tm = sys.argv[2]
  fname = sys.argv[3]

  df = pd.DataFrame()
  desa = gpd.GeoDataFrame.from_file("jadetabek_desa.geojson")
  center = desa.centroid
  for i in range(len(desa)):
      row_desa=desa.loc[i]
      df_ = get_df(start=center[202],end=row_desa.geometry.centroid,dep_time=tm)
      df = pd.concat([df,df_])
      print '\r',str(i),
  df.to_csv(fname,index=False)
  print "Finish exporting "+fname 
