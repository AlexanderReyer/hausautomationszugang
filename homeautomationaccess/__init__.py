from flask import Flask, render_template, request
from data  import articles
import  os,re,telnetlib

app     = Flask(__name__)

Articles = articles()

# Yeelight Port-mapping
#host   = "192.168.178.25"
#port   = 55443
host    = "marssonde.ddns.net"
port    = 80
params  = ""

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

@app.route('/main', methods=["GET", "POST"])
def homepage():
    #return "Hi there, how ya doin?"
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


if __name__ == "__main__":
    app.run(debug=True)
