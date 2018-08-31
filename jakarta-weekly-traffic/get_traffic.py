import pandas as pd
import numpy as np
import urllib2
import json
import pickle
import datetime as dt
from apscheduler.schedulers.blocking import BlockingScheduler
import ssl

def get_traffic():
    app_id = "your_app_id"
    app_code = "your_app_code"
    fname=str(dt.datetime.now())[:19].replace(":","-")
    base="https://traffic.cit.api.here.com/traffic/6.2/flow.json"+\
    "?app_id="+app_id+\
    "&app_code="+app_code+\
    "&bbox=-6.077811,106.559667;-6.665355,107.146117"+\
    "&responseattributes=sh,fc"
    try:
        gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        response = urllib2.urlopen(base,context=gcontext)
        data=json.load(response)
        with open(fname+".p", 'wb') as fp:
            pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)
        print "Success "+fname
    except:
        print "Failed "+fname

if __name__=="__main__":
  sched = BlockingScheduler()
  sched.add_job(get_traffic, 'cron', day_of_week='*', hour='*', 
                minute='0,30')
  sched.start()
