#!/usr/bin/env python
# -*- coding: utf-8 -*-

# create separated thread to fetch metric data from data source
# because I want to access to data source only onetime for many metrics.

import sys
import traceback
import os
import threading
import time

descriptors = list()
Desc_Skel   = {}
_Worker_Thread = None
_Lock = threading.Lock() # synchronization lock
Debug = False

# FIXME modify as you like
Param_Keys = ["device", "host"]

def dprint(f, *v):
    if Debug:
        print >>sys.stderr, "DEBUG: "+f % v

class UpdateMetricThread(threading.Thread):

    def __init__(self, params):
        threading.Thread.__init__(self)
        self.running      = False
        self.shuttingdown = False
        self.prefix       = params["prefix"]
        self.refresh_rate = int(params["refresh_rate"])
        self.metric       = {}

        self.p = {}
        for k in Param_Keys:
            if k in params:
                self.p[k] = params[k]
            else:
                self.p[k] = ""

    def shutdown(self):
        self.shuttingdown = True
        if not self.running:
            return
        self.join()

    def run(self):
        self.running = True

        while not self.shuttingdown:
            _Lock.acquire()
            self.update_metric()
            _Lock.release()
            time.sleep(self.refresh_rate)

        self.running = False

    def update_metric(self):
        # FIXME modify as you like
        self.metric["foo"] = 8
        self.metric["bar"] = 9

    def metric_of(self, name):
        val = 0
        if name in self.metric:
            _Lock.acquire()
            val = self.metric[name]
            _Lock.release()
        return val

def metric_init(params):
    global descriptors, Desc_Skel, _Worker_Thread, Debug

    print '[skel_thread] FIXME'
    print params

    # initialize skeleton of descriptors
    # max value of uint is 4294967295(4G)? because uint cast into unsigned int.
    # ref: gmond/modules/python/mod_python.c

    # FIXME modify as you like
    Desc_Skel = {
        'name'        : 'FIXME TBD',
        'call_back'   : metric_of,
        'time_max'    : 60,
        # must adjust value of "value_type" and "format"
        'value_type'  : 'uint', # string | uint | float | double
        'format'      : '%d',   # %s     | %d   | %f    | %f
        'units'       : 'FIXME',
        'slope'       : 'FIXME zero|positive|negative|both',
        'description' : 'FIXME TBD',
        'groups'      : 'FIXME',
        }

    if "debug" in params:
        Debug = params["debug"]
    dprint("%s", "Debug mode on")

    if "prefix" not in params:
        params["prefix"] = os.path.splitext(os.path.basename(__file__))[0]
    dprint("prefix: %s", params["prefix"])

    if "refresh_rate" not in params:
        params["refresh_rate"] = 10

    _Worker_Thread = UpdateMetricThread(params)
    _Worker_Thread.start()
    _Worker_Thread.update_metric()

    # IP:HOSTNAME
    if "spoof_host" in params:
        Desc_Skel["spoof_host"] = params["spoof_host"]

    # FIXME modify as you like
    descriptors.append(create_desc(Desc_Skel, {
                "name"       : params["prefix"]+"_foo",
                "value_type" : "float",
                "format"     : "%.3f",
                "units"      : "req/sec",
                "description": "request per second",
                }))
    descriptors.append(create_desc(Desc_Skel, {
                "name"       : params["prefix"]+"_bar",
                "value_type" : "uint",
                "format"     : "%d",
                "units"      : "bytes/sec",
                "description": "byte per sec",
                }))

    return descriptors

def create_desc(skel, prop):
    d = skel.copy()
    for k,v in prop.iteritems():
        d[k] = v
    return d

def metric_of(name):
    return _Worker_Thread.metric_of(name)

def metric_cleanup():
    _Worker_Thread.shutdown()

# for deubgging on CUI
if __name__ == '__main__':
    try:
        params = {
            "device"       : "eth0",
            "host"         : "localhost",
            #
            "refresh_rate" : 5,
            "debug"        : True,
            }
        metric_init(params)

  #       for d in descriptors:
  #           print '''  metric {
  #   name  = "%s"
  #   title = "%s"
  #   value_threshold = 0
  # }''' % (d["name"], d["description"])

        while True:
            for d in descriptors:
                v = d['call_back'](d['name'])
                print ('value for %s is '+d['format']) % (d['name'],  v)
            os._exit(1)
            time.sleep(5)
    except KeyboardInterrupt:
        time.sleep(0.2)
        os._exit(1)
    except StandardError:
        traceback.print_exc()
        os._exit(1)
