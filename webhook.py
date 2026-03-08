from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/deploy", methods=["POST"])
def deploy():
    subprocess.Popen(["C:\\Users\\adria\\Documents\\Porygon3\\Porygon3\\deploy.bat"])
    return "Deploying", 200

app.run(host="0.0.0.0", port=5000)