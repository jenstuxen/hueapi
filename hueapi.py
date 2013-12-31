#!/usr/bin/python
import httplib2
import urllib
import json
import time
import random
import datetime

h = httplib2.Http(".cache")
API="/api"
USERNAME="/newdeveloper/"
URL="http://<IP>"+API+USERNAME

class Constructor(object):
    def __init__(self,*initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

class Hue(Constructor):

    def __init__(self,*initial_data, **kwargs):
        super(Hue,self).__init__(initial_data, kwargs)

    def toJSON(self):
        def d(o):
            hue_dict = dict(o.__dict__.items())
            for k,v in o.__dict__.iteritems():
                if k.startswith('toJson'):
                    hue_dict.pop(k,None)
                if v==None:
                    hue_dict.pop(k,None)
                if k in ["light_id","schedule_id","group_id"]:
                    hue_dict.pop(k,None)


            return hue_dict

        return json.dumps(self, default=d)

class Light(Hue):
    ct = None #kelvin uint16, 153: 6500K, 500: 2000K
    hue = None #0-65535 (0: red, 65535: red, 25500: green, 46920: blue
    sat = None #saturation 0-255
    on = None #bool
    xy = None #list of float 4
    alert = None #String, none,select,lselect
    effect = None #String
    colormode = None #String hs=hue,xy=XY,ct=CT
    reachable = None #bool
    light_id = 0
    transition_time = 4 #transistion time in 100 of ms
    name = None

    def __init__(self,*initial_data, **kwargs):
        super(Light,self).__init__(*initial_data, **kwargs)

    @property
    def url(self): return 'lights/'+str(self.light_id)

    @property
    def state_url(self): return self.url+"/state/"

    @property 
    def kelvin(): return int(self.ct)*1000000

    @kelvin.setter
    def kelvin(self,value): self.ct = int(value/1000000)

    def load_state(self):
        code, content = call_api(self.url,"GET")

        content_json = json.loads(content)
        for k,v in content_json["state"].iteritems():
            setattr(self, k, v)

    def set_state(self):
        return call_api_data(self.state_url,'PUT',self.toJSON())
    @property
    def command(self):
        return Command(address=API+USERNAME+self.state_url,method='PUT',body=self.toJSON())


class Group(Hue):
    group_id = 0
    name = None

    def __init__(self,*initial_data, **kwargs):
        Hue.__init__(initial_data, kwargs)

    @property
    def url(self): return 'groups/'+self.group_id

    @property 
    def action(self): return self.url+'action/'

class Command(Hue):
    address = None
    method = None
    body = None

    def __init__(self,address,method,body):
        self.address = address
        self.method = method
        self.body = json.loads(body)

class Schedule(Hue):
    name = None
    description = None
    _command = None

    def __init__(self,*initial_data, **kwargs):
        super(Schedule,self).__init__(*initial_data, **kwargs)

    @property
    def command(self): return self._command

    @command.setter
    def command(self,value): self._command = value

    @property 
    def time(self): return self._time.strftime("%Y-%m-%dT%H:%M:%S")
    @time.setter
    def time(self,value): self._time = value

    def toJSON(self):
        return json.dumps({
            'name':self.name,
            'description':self.description,
            'command':self.command.__dict__,
            'time':self.time},indent=2)

    @property 
    def url(self): return URL+"/schedules/"

    def make(self):
        a,b = call_api_data(self.url,'POST',self.toJSON())
        time.sleep(0.1)
        return a,b

def call_api(method,requestType,**kwargs):
    url = URL+method

    data = dict()
    for k,val in kwargs.iteritems(): 
        data[k] = val

    if len(data.items()) == 0:
        return h.request(url,requestType)

    return h.request(uri=url,method=requestType,body=json.dumps(data))

def call_api_data(method,requestType,data):
    url = URL+method
    return h.request(url,requestType,data)

def turn_on(light):
    light.on = True
    light.set_state()

def turn_off(light):
    light.on = False
    light.set_state()

def light(l,**kwargs):
    return call_api('lights/'+str(l)+'/state','PUT',**kwargs)

def group(g,**kwargs):
    return call_api("groups/%s/%s" % (str(g),'state'), "PUT", **kwargs)

def get_lights():
    def d(l):
        return Light(light_id=l[0])
    return map(d,json.loads(call_api('lights/','GET',)[1]).items())

def get_groups():
    return json.loads(call_api('groups/','GET')[1])

def get_light_ids():
    return map(lambda x: x[0],get_lights())
def getLightNames():
    return map(lambda x: x[1],get_lights())

def delete_schedule(schedule_id):
    call_api("schedules/"+schedule_id,"DELETE")

def delete_all_schedules():
    for s in get_schedules():
        yield s.delete()

def get_schedules():
    def d(l):
        return Schedule(schedule_id=l[0],name=l[1])
    return map(d,json.loads(call_api('schedules/','GET',)[1]).items())


def random_light(light):
    pass

def random_brightness(light):
    pass

def on_off(light):
    random.choice(turn_on,turn_off)(light)

def on_off_loop(lights):
    while True:
        time.sleep(0.25)
        sw = True
        for light in lights:
            light.on = sw
            sw = not sw

if __name__ == "__main__":
    lights = get_lights()

    for light in lights:
        light.colormode = "ct"
        light.ct = (1000000/2500)
        light.bri = 255
        light.on = True
        #light.transition_time = 1
        print light.toJSON()
        print light.set_state()[1]
        time.sleep(0.1)
        brightness = brightness + 1
            
    
    print delete_all_schedules()
    sched = Schedule(name="TEST",description="test of schedule")
    lights[0].on = True
    lights[0].bri = 255
    lights[0].ct = (1000000/6400)

    sched.command = lights[0].command
    sched.time = datetime.datetime.now()+datetime.timedelta(seconds=10)
    print sched.toJSON()
    print sched.make()
    print get_schedules()
