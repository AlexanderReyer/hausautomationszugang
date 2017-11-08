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
from    flask import make_response
import  json


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
def source():
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    telnet.write('{ "id": 1, "method": "set_power", "params":["on", "smooth", 500]} \r\n'.encode())
    #out = telnet.read_all()
    out = telnet.read_until("\r\n".encode(), 1)
    print(out)
    telnet.close()
    #html = 'Hello World!'
    return out
    eingabe = input("drucke return zum Ausschalten.")

@app.route('/off', methods=['GET', 'POST'])
def sourceoff():
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    telnet.write('{ "id": 1, "method": "set_power", "params":["off", "smooth", 500]} \r\n'.encode())
    #out = telnet.read_until(b"DB>", 5)
    #out = telnet.read_all()
    out = telnet.read_until("\r\n".encode(), 1)
    print(out)
    #telnet.write(b'quit\r\n')
    print("schliesse Verbindung")
    telnet.close()
    return out

if __name__ == '__main__':
    serverport = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % serverport)

    app.run(debug=False, port=serverport, host='0.0.0.0')
