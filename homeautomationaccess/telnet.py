# -*- coding:utf8 -*-
# !/usr/bin/env python
#
# Xiaomi Yeelight switching via
# wifi and TCP at port 55443
# 6 nov 2017 Alexander Reyer
#
# https://docs.python.org/2/library/telnetlib.html
#
# RouterDynDNS -Port-> LanIP:Port (ESP8266)
#
# Google Assistant -> Dialogflow -Json-> Heroku -DynDNS-Portmapping-> LANDevice
# LANDevice -SenseValue-> Heroku -Json-> Dialogflow -> Google Assistant
#
# json
# actors:  light
#          set color, brightness, power
# actors:  Yeelight
##      support: set_default set_power toggle set_bright start_cf stop_cf
#          set_scene cron_add cron_del set_ct_abx set_rgb set_hsv set_adjust
#          adjust_bright adjust_ct adjust_color set_music set\r\n
#          -----------------
# actors:  socket
#          toggle, turn on off
#          ---------------------------------
# sensors: light
#          power, color, ID, IP, Port
#          Dialogflow-Name    <-> Telnet-IP, Port from Router
#          Dialogflow-Command <-> Xiaomi-Command
# sensors: Yeelight
##         HTTP/1.1 200 OK\r\n
##         Cache-Control: max-age=3584\r\n
##         Date: \r\n
##         Ext: \r\n
##         Location: yeelight://192.168.178.25:55443\r\n
##         Server: POSIX UPnP/1.0 YGLC/1\r\n
##         id: 0x00000000036f01d3\r\n
##         model: color\r\n
##         fw_ver: 57\r\n
##      support: get_prop start_cf stop_cf cron_get
# {"id":1,"method":"get_prop","params":["power", "not_exist", "bright"]}
#
##         power: off\r\n
##         bright: 1\r\n
##         color_mode: 2\r\n
##         ct: 2700\r\n
##         rgb: 16711680\r\n
##         hue: 359\r\n
##         sat: 100\r\n
##         name: \r\n'
#          -----------------
# sensors: socket
#          power, ID, IP, Port


import  os,re,telnetlib
from    flask import Flask
from    flask import request
from    flask import make_response, render_template
from flask_bootstrap import Bootstrap
import  json
import socket       # ssdp uPnP searching for yeelight

msg = \
    'M-SEARCH * HTTP/1.1\r\n' \
    'HOST:239.255.255.250:1982\r\n' \
    'ST:upnp:rootdevice\r\n' \
    'MX:2\r\n' \
    'MAN:"ssdp:discover"\r\n' \
    'ST: wifi_bulb' \
    '\r\n'


# Yeelight Port-mapping
#host       = "192.168.178.25"
#port       = 55443
host        = "marssonde.ddns.net"  # connect to device via port mapping
hostssdp    = '239.255.255.250'     # search for uPnP device
port        = 80
portssdp    = 1982                  # yeelight ssdp-port instead of 1900

'''
1. action    -> licht
2.       Name      -> portmapping-Name
3.            parameter -> device-command
4.       sense value -> parameter
5. results -> json

{
  "id": "3f80cead-daeb-4428-82c8-eabbbfc978d9",
  "timestamp": "2017-11-07T21:19:56.054Z",
  "lang": "de",
  "result": {
    "source": "agent",
    "resolvedQuery": "schalte das wohnzimmerlicht an",
    "action": "lightaction",                            licht
    "actionIncomplete": false,
    "parameters": {
      "artikel": "das",
      "lichtname": "wohnzimmerdeckenlampe",             marssonde.ddns.net:80
      "lichtzustand": "an"                              Yeelight set_power
    },
    "contexts": [],
    "metadata": {
      "intentId": "3d587ba7-8c46-4526-888f-84bf586a02ef",
      "webhookUsed": "true",
      "webhookForSlotFillingUsed": "false",
      "webhookResponseTime": 121,
      "intentName": "lichtintent"
    },
    "fulfillment": {
      "speech": "webhook wurde aufgerufen",
      "source": "marssonde.ddns.net:80",                Yeelight at ...25:55443
      "displayText": "webhook wurde aufgerufen",
      "messages": [
        {
          "type": 0,
          "speech": "webhook wurde aufgerufen"
        }
      ]
    },
    "score": 1
  },
  "status": {
    "code": 200,
    "errorType": "success"
  },
  "sessionId": "3e424dac-92e6-43f2-ac84-e9d50b0845e3"
}'''
app = Flask(__name__)
bootstrap = Bootstrap(app) # Webdesign-features

# -------- webhook for dialogflow ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))
    #processRequest(req)
    #return "webhook action msg"
    res =  {
            "speech": "webhook wurde aufgerufen",
            "displayText": "webhook wurde aufgerufen",
            # "data": data,
            # "contextOut": [],
            "source": "marssonde.ddns.net:80"
            }
    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def processRequest(req):
    if req.get("result").get("action") != "":
        return {}
    res = "action"
    return res

# -------- INDEX and main template ----------
# JSON objects will be sent to device via TCP
#
# { "id":       1,                         int
#   "method":   "set_power",               str
#   "params":   ["on", "smooth", 500]      array
# }
#
@app.route('/', methods=['GET', 'POST'])
def index():
    # values containing device states:
    power       = 0
    rgb         = 0
    # following button-states contain str "pressed" or None
    get_prop    = request.form.get("get_prop")
    set_power   = request.form.get("set_power")
    set_rgb     = request.form.get("set_rgb")
    toggle      = request.form.get("toggle")
    response    = ""   # contains the return str sent back by the device
        
    if request.method == "POST":
        print(request.form)
        # get form values that shall change the device state
        power = request.form.get("powertext")
        rgb = request.form.get("rgbtext")

    print("Buttons+Texts:", set_power, power, set_rgb, rgb, toggle)
    #return "debug" # -- Debug --


    # get_prop -----------------------------
    # Usage: This method is used to retrieve current property of smart LED.
    # Parameters:              1 to N.
    # The parameter is a list of property names and the response contains a list of corresponding property values.
    # If the requested property name is not recognized by smart LED, then a empty string value ("") will be returned.
    # Request Example:     {"id":1,"method":"get_prop","params":["power", "not_exist", "bright"]}
    # Response Example:  {"id":1, "result":["on", "", "100"]}
    # NOTE:                          All the supported properties are defined in table 4-2, section 4.3
    if get_prop is not None:
        print("yeelight power: ", power, " rgb: ", rgb)
        print(get_prop)

   
    # set_power -----------------------------
    if set_power is not None: #!= "":
        if "0" != str(power): #request.form["powertext"]:
            params = '["on", "smooth", 500]'
        else:
            params = '["off", "smooth", 500]'
        response = telnettodevice('{ "id": 1, "method": "set_power", "params":' + params + '} \r\n')
        
    # set_rgb ------------------------------
    if set_rgb is not None: # decimal integer ranges from 0 to 16777215 (hex: 0xFFFFFF). 
        params = request.form["rgbtext"]
        response = telnettodevice('{"id":1,"method":"set_rgb","params":[' + params + ', "smooth", 500]} \r\n')
        
    # toggle -----------------------------
    if toggle is not None:
        response = telnettodevice('{"id":1,"method":"toggle","params":[]} \r\n')

    return render_template("main.html", power = power, test = set_power, rgb = rgb, response = response)

# ----------------------------------------
# -------- telnet TCP to device ----------
def telnettodevice(writetext = ""):
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    #telnet.write('{ "id": 1, "method": "set_power", "params":["on", "smooth", 500]} \r\n'.encode())
    print(writetext.encode())
    telnet.write(writetext.encode())
    #out = telnet.read_all()
    response = telnet.read_until("\r\n".encode(), 1)
    print(response)
    telnet.close()
    return response


# -------- turn on yeelight lamp ----------
@app.route('/on', methods=['GET', 'POST'])
def sourceon():
    response = telnettodevice('{ "id": 1, "method": "set_power", "params":["on", "smooth", 500]} \r\n')
    return render_template("main.html", response = response)

# -------- ssdp yeelight lamp LAN ---------
# use ssdp-ip in lan to search for uPnP device
@app.route('/ssdp', methods=['GET', 'POST'])
def ssdp_lan():
    #
    # https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/
    #
    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.settimeout(1)
    s.sendto(msg.encode(), (hostssdp, portssdp) )

    ''' Response:
    addr = ('192.168.178.25', 49156) b'

    HTTP/1.1 200 OK\r\n
    '''
    try:
        while True:
            data, addr = s.recvfrom(65507)
            print ("addr: ", addr, "\r\ndata ", data)
    except socket.timeout:
        pass
    return render_template("main.html", response = data)

# -------- ssdp yeelight lamp GLOBAL -------
# use port mapping from fritzbox to connect to ssdp-IP-Addr
@app.route('/ssdpglobal', methods=['GET', 'POST'])
def ssdpglobal():
    #
    # https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/
    #
    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.settimeout(1)
    s.sendto(msg.encode(), (host, portssdp) )

    try:
        while True:
            data, addr = s.recvfrom(65507)
            print ("addr: ", addr, "\r\ndata ", data)
    except socket.timeout:
        pass
    ''' Response:

    HTTP/1.1 200 OK\r\n
    Cache-Control: max-age=3584\r\n
    Date: \r\n
    Ext: \r\n
    Location: yeelight://192.168.178.25:55443\r\n
    Server: POSIX UPnP/1.0 YGLC/1\r\n
    id: 0x00000000036f01d3\r\n
    model: color\r\n
    fw_ver: 57\r\n
    support: get_prop set_default set_power toggle set_bright start_cf stop_cf set_scene cron_add cron_get cron_del set_ct_abx set_rgb set_hsv set_adjust adjust_bright adjust_ct adjust_color set_music set\r\n
    power: off\r\n
    bright: 1\r\n
    color_mode: 2\r\n
    ct: 2700\r\n
    rgb: 16711680\r\n
    hue: 359\r\n
    sat: 100\r\n
    name: \r\n'
    '''
    response = {}
    #print ("str data: ", str(data).split("\\r\\n") )
    words = str(data).split("\\r\\n")
    for word in words:
        #print(word)
        if 0 < str(word).find(":"):
            response[word.split(":",1)[0]] = word.split(":",1)[1]

    print(response)
    print("power: ", response["power"], " location: ", response["Location"])

    ipad, port =  response["Location"].split("//")[1].split(":")
    print("ip: ", ipad, " port: ", port)
    return render_template("main.html", response = response)
    #return make_response(str(data).encode() + "<br>".encode() + str(addr).encode())

# -------- turn off yeelight lamp ----------
@app.route('/off', methods=['GET', 'POST'])
def sourceoff():
    response = telnettodevice('{ "id": 1, "method": "set_power", "params":["off", "smooth", 500]} \r\n')
    return render_template("main.html", response = response)

# -------- MAIN LOCALHOST SERVER  ----------
if __name__ == '__main__':
    serverport = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % serverport)

    app.run(debug=True, port=serverport) #, host='0.0.0.0')
