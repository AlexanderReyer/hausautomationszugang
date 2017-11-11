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
#host = "192.168.178.25"
#port = 55443
host = "marssonde.ddns.net"
port = 80


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

@app.route('/', methods=['GET', 'POST'])
def index():
    power = 0
    rgb = 0
    set_power = ""
    set_rgb = ""
    toggle = ""
    response = ""
        
    if request.method == "POST":
        print(request.form)
        power = request.form["powertext"]
        rgb = request.form["rgbtext"]
        if request.form.get("set_power"):
            set_power = request.form["set_power"]
        if request.form.get("set_rgb"):
            set_rgb = request.form["set_rgb"]
        if request.form.get("toggle"):
            toogle = "1"

    # set_power -----------------------------
    if set_power != "":
        if "0" != request.form["powertext"]:
            params = '["on", "smooth", 500]'
        else:
            params = '["off", "smooth", 500]'
        response = telnettodevice('{ "id": 1, "method": "set_power", "params":' + params + '} \r\n')
        
    if set_rgb != "": # decimal integer ranges from 0 to 16777215 (hex: 0xFFFFFF). 
        params = request.form["rgbtext"]
        response = telnettodevice('{"id":1,"method":"set_rgb","params":[' + params + ', "smooth", 500]} \r\n')
        
    if toggle != "":
        response = telnettodevice('{"id":1,"method":"toggle","params":[]} \r\n')

    #print("Button Wert set_power: ", set_power)
    return render_template("main.html", power = power, test = set_power, rgb = rgb, response = response)


def telnettodevice(writetext = ""):
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    #telnet.write('{ "id": 1, "method": "set_power", "params":["on", "smooth", 500]} \r\n'.encode())
    telnet.write(writetext.encode())
    #out = telnet.read_all()
    response = telnet.read_until("\r\n".encode(), 1)
    print(response)
    telnet.close()
    return response


@app.route('/on', methods=['GET', 'POST'])
def sourceon():
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    telnet.write('{ "id": 1, "method": "set_power", "params":["on", "smooth", 500]} \r\n'.encode())
    #out = telnet.read_all()
    response = telnet.read_until("\r\n".encode(), 1)
    print(response)
    telnet.close()
    return render_template("main.html", response = response)
    #return response

@app.route('/ssdp', methods=['GET', 'POST'])
def ssdp():
    #
    # https://www.electricmonk.nl/log/2016/07/05/exploring-upnp-with-python/
    #
    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.settimeout(1)
    s.sendto(msg.encode(), ('239.255.255.250', 1982) )

    try:
        while True:
            data, addr = s.recvfrom(65507)
            print ("addr: ", addr, "\r\ndata ", data)
    except socket.timeout:
        pass
    ''' Response:
    addr = ('192.168.178.25', 49156) b'

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

@app.route('/off', methods=['GET', 'POST'])
def sourceoff():
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    telnet.write('{ "id": 1, "method": "set_power", "params":["off", "smooth", 500]} \r\n'.encode())
    #out = telnet.read_until(b"DB>", 5)
    #out = telnet.read_all()
    response = telnet.read_until("\r\n".encode(), 1)
    print(response)
    #telnet.write(b'quit\r\n')
    print("schliesse Verbindung")
    telnet.close()
    return render_template("main.html", response = response)
    #return out

if __name__ == '__main__':
    serverport = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % serverport)

    app.run(debug=True, port=serverport, host='0.0.0.0')
