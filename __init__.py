from flask import Flask, render_template, request
import  os,re,telnetlib

app     = Flask(__name__)

# Yeelight Port-mapping
#host   = "192.168.178.25"
#port   = 55443
host    = "marssonde.ddns.net"
port    = 80
params  = ""

@app.route('/main', methods=["GET", "POST"])
def homepage():
    #return "Hi there, how ya doin?"
    if request.method == "POST":
        print(request.form)
        power = request.form["powertext"]
        set_power = request.form["set_power"]
    else:
        power = 0
        set_power = ""

    # set_power -----------------------------
    if set_power != "":
        if "0" != request.form["powertext"]:
            params = '["on", "smooth", 500]'
        else:
            params = '["off", "smooth", 500]'
        telnettodevice('{ "id": 1, "method": "set_power", "params":' + params + '} \r\n')
        
    print("Button Wert set_power: ", set_power)
    return render_template("main.html", power = power, test = set_power)


def telnettodevice(writetext = ""):
    print("oeffne mit telnetlib ", host, ":", port)
    telnet = telnetlib.Telnet()
    telnet.open(host, port, 3)
    #telnet.write('{ "id": 1, "method": "set_power", "params":["on", "smooth", 500]} \r\n'.encode())
    telnet.write(writetext.encode())
    #out = telnet.read_all()
    out = telnet.read_until("\r\n".encode(), 1)
    print(out)
    telnet.close()


if __name__ == "__main__":
    app.run(debug=True)
