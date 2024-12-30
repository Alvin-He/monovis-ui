import flask
import json
import ntcore
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)

nt = ntcore.NetworkTableInstance.getDefault()

@app.route("/api/config/nt-team", methods=["POST"])
def nt_team():
    jData = flask.request.get_json(); 
    if (not jData): return "Bad Request Type", 400
    
    if (not "team" in jData): return "Bad Request Payload", 400
    team = int(jData["team"])
    nt.setServerTeam(team)

    return "Team Number Successfully Set", 200

@app.route("/api/config/nt-addr", methods=["POST"])
def nt_addr():
    jData = flask.request.get_json(); 
    if (not jData): return "Bad Request Type", 400

    if (not "addr" in jData): return "Bad Request Payload", 400
    addr = jData["addr"]
    
    if ("port" in jData): 
        port = int(jData["port"])
        nt.setServer(addr, port)

        return f"NT Server Address Successfully Set to {addr}, Port set to {port}", 200
    else:
        nt.setServer(addr)

        return f"NT Server Address Successfully Set to {addr}, Using Default Port", 200



nt_robotPosTable: ntcore.NetworkTable = nt.getTable("Vision").getSubTable("RobotPos")
robotPos_x = nt_robotPosTable.getDoubleTopic("x").subscribe(0)
robotPos_y = nt_robotPosTable.getDoubleTopic("y").subscribe(0)
robotPos_r = nt_robotPosTable.getDoubleTopic("r").subscribe(0)
@app.route("/api/robot-pose", methods=["GET"])
def robot_pose(): 
    if (not flask.request.method == "GET"): return "Bad Request", 400 

    if (not nt.isConnected()): 
        return "Data Not Yet Available", 503

    if (not robotPos_x.exists() or 
        not robotPos_y.exists() or 
        not robotPos_r.exists()): 
        return "Data Not Yet Available", 503

    return {"x": robotPos_x.get(), "y": robotPos_y.get(), "r": robotPos_r.get()}, 200


frame: bytes = None
@app.route("/api/cam/upload", methods=["PUT"])
def upload_cam(): 
    global frame
    if (not flask.request.method == "PUT"): return "Bad Request", 400
    
    frame = flask.request.get_data(cache=False)

    return f"successfully uploaded frame of size {len(frame)}"

@app.route("/api/cam/download", methods=["GET"])
def download_cam():
    global frame
    if (not flask.request.method == "GET"): return "Bad Request", 400

    if (frame == None): return "No Yet Aviliable", 404

    resp = flask.make_response()
    resp.status_code = 200
    resp.headers["Content-Type"] = "application/octet-stream"
    resp.set_data(frame)
    resp.calculate_content_length()

    return resp; 


