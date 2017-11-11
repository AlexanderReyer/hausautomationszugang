import socket

msg = \
    'M-SEARCH * HTTP/1.1\r\n' \
    'HOST:239.255.255.250:1982\r\n' \
    'ST:upnp:rootdevice\r\n' \
    'MX:2\r\n' \
    'MAN:"ssdp:discover"\r\n' \
    'ST: wifi_bulb' \
    '\r\n'
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
