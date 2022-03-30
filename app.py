import json
import subprocess
import time

from flask import Flask, flash, redirect, render_template, request

env = json.load(open('env.json'))

app = Flask(__name__)
app.debug = True
app.secret_key = env['SECRET']


@app.route('/')
def index():
    pgrep = subprocess.run("pgrep openconnect", shell=True)
    ip = ''
    if pgrep.returncode != 0:
        status = 'disconnected'
    else:
        ip = str(subprocess.check_output("/sbin/ifconfig tun0 | grep 'inet ' | cut -d: -f2 | awk '{ print $2}'", shell=True), 'UTF-8')
        status = 'connected'
    return render_template('index.html', title='VPN', status=status, ip=ip)


@app.route('/conn', methods=["GET", "POST"])
def conn():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        status = subprocess.run(f"echo {password}| openconnect -u {user} -b {env['ADDRESS']}", shell=True)
        if status.returncode == 0:
            while subprocess.run("ifconfig -a | grep tun0", shell=True).returncode != 0:
                time.sleep(0.5)
            subprocess.run("route del -net 0.0.0.0 gw 0.0.0.0 netmask 0.0.0.0 dev tun0", shell=True)
            subprocess.run("route add -net 10.0.0.0 gateway 10.8.111.0 netmask 255.0.0.0 dev tun0", shell=True)
            flash('Authentication succeed', 'success')
            return redirect('/')
        else:
            flash('Authentication failed', 'danger')
            return redirect('/')
    else:
        return redirect('/')


@app.route('/disc')
def disc():
    pgrep = subprocess.run("pgrep openconnect", shell=True)

    if pgrep.returncode == 0:
        subprocess.run("pkill -SIGINT openconnect", shell=True)
        time.sleep(1)
        return redirect('/')
    else:
        return redirect('/')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, ssl_context=('/etc/ssl/certs/cert.pem', '/etc/ssl/private/key.pem'))
