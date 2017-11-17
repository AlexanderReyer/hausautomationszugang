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
#		   set color, brightness, power
# actors:  Yeelight
##		support: set_default set_power toggle set_bright start_cf stop_cf
#		   set_scene cron_add cron_del set_ct_abx set_rgb set_hsv set_adjust
#		   adjust_bright adjust_ct adjust_color set_music set\r\n
#		   -----------------
# actors:  socket
#		   toggle, turn on off
#		   ---------------------------------
# sensors: light
#		   power, color, ID, IP, Port
#		   Dialogflow-Name	  <-> Telnet-IP, Port from Router
#		   Dialogflow-Command <-> Xiaomi-Command
# sensors: Yeelight
##		   HTTP/1.1 200 OK\r\n
##		   Cache-Control: max-age=3584\r\n
##		   Date: \r\n
##		   Ext: \r\n
##		   Location: yeelight://192.168.178.25:55443\r\n
##		   Server: POSIX UPnP/1.0 YGLC/1\r\n
##		   id: 0x00000000036f01d3\r\n
##		   model: color\r\n
##		   fw_ver: 57\r\n
##		support: get_prop start_cf stop_cf cron_get
# {"id":1,"method":"get_prop","params":["power", "not_exist", "bright"]}
#
##		   power: off\r\n
##		   bright: 1\r\n
##		   color_mode: 2\r\n
##		   ct: 2700\r\n
##		   rgb: 16711680\r\n
##		   hue: 359\r\n
##		   sat: 100\r\n
##		   name: \r\n'
#		   -----------------
# sensors: socket
#		   power, ID, IP, Port


import	os,re,telnetlib
from	flask import Flask
from	flask import request
from	flask import make_response, render_template
from flask_bootstrap import Bootstrap
import	json
import socket		# ssdp uPnP searching for yeelight

msg = \
	'M-SEARCH * HTTP/1.1\r\n' \
	'HOST:239.255.255.250:1982\r\n' \
	'ST:upnp:rootdevice\r\n' \
	'MX:2\r\n' \
	'MAN:"ssdp:discover"\r\n' \
	'ST: wifi_bulb' \
	'\r\n'


# Yeelight Port-mapping
#host		= "192.168.178.25"
#port		= 55443
host		= "marssonde.ddns.net"	# connect to device via port mapping
hostssdp	= '239.255.255.250'		# search for uPnP device
port		= 80
portssdp	= 1982					# yeelight ssdp-port instead of 1900

paramnames = {"power":"on",
			  "bright":100,
			  "ct":1700,
			  "rgb":16777215,
			  "hue":359,
			  "sat":100,
			  "color_mode":1,
			  "flowing":1,
			  "delayoff":60,
			  "flow_params":2,
			  "music_on":0,
			  "name":"yeelight"
			  }
'''
"bg_power":0,
"bg_flowing":"off",
"bg_flow_params":"off",
"bg_ct":0,
"bg_lmode":2,
"bg_bright":100,
"bg_rgb":12777,
"bg_hue":2,
"bg_sat":100,
"nl_br":100}
'''

effect		= "smooth"
duration	= 500
'''
Property Name Possible value
power on: smart LED is turned on  /	 off: smart LED is turned off
bright Brightness percentage. Range 1 ~ 100
ct Color temperature. Range 1700 ~ 6500(k)
rgb Color. Range 1 ~ 16777215
hue Hue. Range 0 ~ 359
sat Saturation. Range 0 ~ 100
color_mode 1: rgb mode	 /	 2: color temperature mode / 3: hsv mode
flowing 0: no flow is running  /  1:color flow is running
delayoff The remaining time of a sleep timer. Range 1 ~ 60 (minutes)
flow_params Current flow parameters (only meaningful when 'flowing' is 1)
music_on 1: Music mode is on / 0: Music mode is off
name The name of the device set by “set_name” command
bg_power Background light power status
bg_flowing Background light is flowing
bg_flow_params Current flow parameters of background light
bg_ct Color temperature of background light
bg_lmode 1: rgb mode   /   2: color temperature mode / 3: hsv mode
bg_bright Brightness percentage of background light
bg_rgb Color of background light
bg_hue Hue of background light
bg_sat Saturation of background light
nl_br Brightness of night mode light 

'''

'''
1. action	 -> licht
2.		 Name	   -> portmapping-Name
3.			  parameter -> device-command
4.		 sense value -> parameter
5. results -> json

{
  "id": "3f80cead-daeb-4428-82c8-eabbbfc978d9",
  "timestamp": "2017-11-07T21:19:56.054Z",
  "lang": "de",
  "result": {
	"source": "agent",
	"resolvedQuery": "schalte das wohnzimmerlicht an",
	"action": "lightaction",							licht
	"actionIncomplete": false,
	"parameters": {
	  "artikel": "das",
	  "lichtname": "wohnzimmerdeckenlampe",				marssonde.ddns.net:80
	  "lichtzustand": "an"								Yeelight set_power
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
	  "source": "marssonde.ddns.net:80",				Yeelight at ...25:55443
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
			"source": "marssonde.ddns.net:80",
			"received": json.dumps(req, indent=4)
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

@app.route('/colorpicker', methods=['GET', 'POST'])
def colorpicker():
	return render_template("colorpicker.html")

# -------- INDEX and main template ----------
# JSON objects will be sent to device via TCP
#
# { "id":		1,						   int
#	"method":	"set_power",			   str
#	"params":	["on", "smooth", 500]	   array
# }
#
@app.route('/', methods=['GET', 'POST'])
def index():
	# values containing device states:
	power		= 0
	rgb			= 0
	ct_value	= 0
	global effect
	global duration
	# following button-states contain str "pressed" or None
	get_prop	= request.form.get("get_prop")
	set_power	= request.form.get("set_power")
	set_rgb		= request.form.get("set_rgb")
	toggle		= request.form.get("toggle")
	set_ct_abx	= request.form.get("set_ct_abx")
	red			= request.form.get("red")
	green		= request.form.get("green")
	blue		= request.form.get("blue")
	set_bright	= request.form.get("set_bright")
	set_hsv		= request.form.get("set_hsv")
	start_cf	= request.form.get("start_cf")
	stop_cf		= request.form.get("stop_cf")
	set_adjust	= request.form.get("set_adjust")
	cron_get	= request.form.get("cron_get")
	set_default	= request.form.get("set_default")
	cron_del	= request.form.get("cron_del")

	response	= b""	# contains the return str sent back by the device
		
	if request.method == "POST":
		print(request.form)
		# get form values that shall change the device state
		power		= request.form.get("powertext")
		rgb			= request.form.get("rgbtext")
		ct			= request.form.get("cttext")
		effect		= request.form.get("effect")
		duration	= request.form.get("durationtext")
		hue			= request.form.get("huetext")
		sat			= request.form.get("sattext")
		bright		= request.form.get("brighttext")
		color_mode	= request.form.get("color_mode")

	# get_prop -----------------------------
	# Usage: This method is used to retrieve current property of smart LED.
	# Parameters:			   1 to N.
	# The parameter is a list of property names and the response contains a list of corresponding property values.
	# If the requested property name is not recognized by smart LED, then a empty string value ("") will be returned.
	# Request Example:	   {"id":1,"method":"get_prop","params":["power", "not_exist", "bright"]}
	# Response Example:	 {"id":1, "result":["on", "", "100"]}
	# NOTE:							 All the supported properties are defined in table 4-2, section 4.3
	if get_prop is not None:
		params		= ""		 # will contain "power", "bright" a.s.o.
		result		= 0
		response	= 0
		resultindex = 0
		for paramname in paramnames:
			params += "\"" + paramname + "\","
		params = params[:-1]	# remove last comma for array-building in command
		print(params)
		response = telnettodevice('{"id":1,"method":"get_prop","params":[' + params +']}  \r\n')
		print("str(response): ", str(response.decode("ascii"))) #.replace("\r\n", "")
		# b'{"id":1, "result":["off","100","4000","123445","359","100","1","0","0","","0","","","","","","","","","","",""]}\r\n'
		result = json.loads(str(response.decode("ascii")))	# complete json dictionary
		result = result.get("result")						# array of result values
		print("result: ", result)
		for paramname in paramnames:								# "power", "bright" a.s.o
			resultindex = dictionaryindexof(paramnames, paramname)	# index of "power" in dict
			paramnames[paramname] = result[resultindex] # e.g. panms["power"] = result[0] = "on"

		#response = str(response.decode("ascii")) # invisible b' and \r\n
		#return render_template("main.html", paramnames = paramnames, response = response)
	
	# Method:  set_ct_abx
	# Usage: This method is used to change the color temperature of a smart LED.
	# Parameters:  3. "ct_value" is the target color temperature.
	# The type is integer and range is 1700 ~ 6500 (k).
	# "effect" support two values: "sudden" and "smooth".
	# If effect is "sudden", then the color temperature will be changed directly to target value,
	# under this case, the third parameter "duration" is ignored.
	# If effect is "smooth", then the color temperature will be changed to target value in a gradual fashion,
	# under this case, the total time of gradual change is specified in third parameter "duration".
	# "duration" specifies the total time of the gradual changing.
	# The unit is milliseconds. The minimum support duration is 30 milliseconds.
	# Request  Example:	 {"id":1,"method":"set_ct_abx","params":[3500, "smooth", 500]}
	# Response Example:	 {"id":1, "result":["ok"]} NOTE:
	# Only accepted if the smart LED is currently in "on" state. if set_ct_abx is not None:
	if set_ct_abx is not None:
		params = ct + ", \"" + effect + "\", " + duration
		response = telnettodevice('{"id":1,"method":"set_ct_abx","params":[' + params + ']} \r\n')
		paramnames["ct"] = ct
		#return render_template("main.html", response = response, paramnames = paramnames)

   
	# set_power -----------------------------
	if set_power is not None: #!= "":
		response = yeelight_set_power(power)
		paramnames["power"] = power # put sent power value in paramnames
		#paramnames["power"] = json.loads("[" + params + "]")[0] # put sent power value in paramnames
		
	# set_rgb ------------------------------
	if set_rgb is not None: # decimal integer ranges from 0 to 16777215 (hex: 0xFFFFFF).
		print(rgb, effect, duration)
		params = rgb + ', "' + str(effect) + '", ' + str(duration)
		response = telnettodevice('{"id":1,"method":"set_rgb","params":[' + params + ']} \r\n')
		paramnames["rgb"] = rgb
		
	# toggle -----------------------------
	if toggle is not None:
		response = telnettodevice('{"id":1,"method":"toggle","params":[]} \r\n')

	'''
	Method:                     set_hsv 
	Usage:                        This method is used to change the color of a smart LED. 
	Parameters:              4. "hue" is the target hue value, whose type is integer. It should be expressed in 
	decimal integer ranges from 0 to 359.                                      
	"sat" is the target saturation value whose type is integer. It's range is 0 to 100. 
	"effect": Refer to "set_ct_abx" method. "duration": Refer to "set_ct_abx" method. 
	Request Example:   {"id":1,"method":"set_hsv","params":[255, 45, "smooth", 500]} 
	Response Example:  {"id":1, "result":["ok"]} NOTE:                           
	Only accepted if the smart LED is currently in "on" state. 
	'''
	if set_hsv is not None:
		params = hue + ", " + sat + ", \"" + effect + "\", " + duration
		response = telnettodevice('{"id":1,"method":"set_hsv","params":[' + params + ']} \r\n')
		paramnames["hue"] = hue
		paramnames["sat"] = sat
	
	'''
	Method:                     set_bright 
	Usage:                        This method is used to change the brightness of a smart LED. 
	Parameters:              3. "brightness" is the target brightness. The type is integer and ranges from 1 to 100. 
	The brightness is a percentage instead of a absolute value. 100 means maximum brightness while 1 means the minimum brightness.
	"effect": Refer to "set_ct_abx" method. "duration": Refer to "set_ct_abx" method. 
	Request Example:   {"id":1,"method":"set_bright","params":[50, "smooth", 500]} 
	Response Example:  {"id":1, "result":["ok"]} NOTE:  Only accepted if the smart LED is currently in "on" state
	'''
	if set_bright is not None:
		params = bright + ", \"" + effect + "\", " + duration
		response = telnettodevice('{"id":1,"method":"set_bright","params":[' + params + ']} \r\n')
		paramnames["bright"] = bright

	'''
	Method:                      set_default Usage:                         
	This method is used to save current state of smart LED in persistent memory. So if user powers off and then 
	powers on the smart LED again (hard power reset), the smart LED will show last saved state. 
	Parameters:               0. 
	Request Example:   {"id":1,"method":"set_default","params":[]} 
	Response Example:  {"id":1, "result":["ok"]} 
	NOTE: For example, if user likes the current color (red) and brightness (50%) and want to make this state as a 
	default initial state (every time the smart LED is powered), then he can use set_default to do a snapshot. 
	'''
	if set_default is not None:
		response = telnettodevice('{"id":1,"method":"set_default","params":[]} \r\n')
	
	'''
	Method:                      start_cf Usage:                         
	This method is used to start a color flow. Color flow is a series of smart LED visible state changing. 
	It can be brightness changing, color changing or color temperature changing. This is the most powerful command. 
	All our recommended scenes, e.g. Sunrise/Sunset effect is implemented using this method. 
	With the flow expression, user can actually “program” the light effect. 
	Parameters: 3. "count" is the total number of visible state changing before color flow stopped. 
					0 means infinite loop on the state changing.                                       
					"action" is the action taken after the flow is stopped.                                              
					0 means smart LED recover to the state before the color flow started.
					1 means smart LED stay at the state when the flow is stopped.
					2 means turn off the smart LED after the flow is stopped.
					"flow_expression" is the expression of the state changing series. 
	Request Example:   {"id":1,"method":"start_cf","params":[ 4, 2,    "1000, 2, 2700, 100, 
																		500, 1, 255, 10, 
																		5000, 7, 0,0, 
																		500, 2, 5000, 1"]}
	Response Example:  {"id":1, "result":["ok"]} NOTE:                 
	Each visible state changing is defined to be a flow tuple that contains 4 elements: [duration, mode, value, brightness]. 
	A flow expression is a series of flow tuples.  So for above request example, it means: change CT to 2700K & maximum brightness 
	gradually in 1000ms, then change color to red & 10% brightness gradually in 500ms, then stay at this state for 5 seconds, 
	then change CT to 5000K & minimum brightness gradually in 500ms.
	After 4 changes reached, stopped the flow and power off the smart LED.  
 
[duration, mode, value, brightness]: Duration:    Gradual change time or sleep time, in milliseconds, 
minimum value 50. 
Mode:         1 – color, 2 – color temperature, 7 – sleep. Value:          RGB value when mode is 1, CT value when mode is 2, Ignored when mode is 7. Brightness: Brightness value, -1 or 1 ~ 100. Ignored when mode is 7. When this value is -1, brightness in this tuple is ignored (only color or CT change takes effect).  
 
                                                 Only accepted if the smart LED is currently in "on" state. 
 
The logic can be expressed in following pseudo code. 
 +start_cf:   cnt = 0   while true:       if flow_cnt != 0 and cnt >= flow_cnt:           take_stop_action(flow_action)                   break       tuple = get_next_flow_tuple()              # flow tuple will be put in a circular list       apply_effect(tuple)                                 
 # change RGB/CT gradually or sleep 
	'''
	if start_cf is not None:
		#params = "\"" + cfcount + ", " + cfactionafter + ", " + color_mode
		'''
		params = 4 + ", " + 2 + ", \""+1000 + " ," + 2+ ", "+ 2700 + ", " + 100 + ", "+ \
																		500 +", "+ 1 + ", "+ 255+", "+10+", "+ \
																		5000+", "+7+", "+0+","+0+", "+ \
																		500+","+ 2+","+ 5000+","+ 1 + "\""
		'''
		params = "0, 0, \"1000, 2, 2700, 100, 500, 1, 255, 10, 1000, 7, 0,0, 500, 2, 5000, 1 "\
					", 500, 2, 1500, 100"\
				 "\""
		response = telnettodevice('{"id":1,"method":"start_cf","params":[' + params +']} \r\n')
	
	'''
	Method:                      stop_cf Usage:                         
	This method is used to stop a running color flow. Parameters:               0. 
	Request Example:   {"id":1,"method":"stop_cf","params":[]} 
	Response Example:  {"id":1, "result":["ok"]} 
	'''
	if stop_cf is not None:
		response = telnettodevice('{"id":1,"method":"stop_cf","params":[]} \r\n')

	'''
	Method:                      cron_get Usage:                         
	This method is used to retrieve the setting of the current cron job of the specified type. 
	Parameters:                1. "type" the type of the cron job. (currently only support 0). 
	Request Example:     {"id":1,"method":"cron_get","params":[0]} 
	Response Example:  {"id":1, "result":[{"type": 0, "delay": 15, "mix": 0}]} 
	'''
	if cron_get is not None:
		response = telnettodevice('{"id":1,"method":"cron_get","params":[0]} \r\n')
	
	'''
	Method:                      cron_del Usage:                         
	This method is used to stop the specified cron job. 
	Parameters:                1.  "type" the type of the cron job. (currently only support 0).  
	Request Example:     {"id":1,"method":"cron_del","params":[0]} 
	Response Example:  {"id":1, "result":["ok"]} '''
	if cron_del is not None:
		response = telnettodevice('{"id":1,"method":"cron_del","params":[0]} \r\n')

	# calculate red green blue from decimal rgb-value
	red 		= int( int(paramnames.get("rgb")) / 65536)
	green 		= int( (int(paramnames.get("rgb")) - (red*65536)) / 256)
	blue 		= int(paramnames.get("rgb")) - int(red*65536) - int(green*256)
	response 	= str(response.decode("ascii")) # invisible b' and \r\n
	return render_template("main.html", response = response,
						   paramnames = paramnames,
						   effect = effect,
						   duration = duration,
						   red=red,
						   green=green,
						   blue=blue)

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


# ----------------------------------------
# -------- dictionaryindexof -------------
# get index number of dictionary key -----
def dictionaryindexof(dictionary, searchkey):
	index = 0
	for key in dictionary:
		if key == searchkey:
			return index
		index += 1
	return -1

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


# --set_power ------------------
# turn yeelight lamp on or off
def yeelight_set_power(power):
	if "0" != str(power) and "off" != str(power): #request.form["powertext"]:
		params = '"on", "smooth", 500'
	else:
		params = '"off", "smooth", 500'
	return telnettodevice('{ "id": 1, "method": "set_power", "params":[' + params + ']} \r\n')
	
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
