import flask
import json
import time
import sys
import ntcore
from wpimath.geometry import Pose2d, Rotation2d
from flask_cors import CORS
import wpimath.geometry
import wpimath.units

app = flask.Flask(__name__)
CORS(app)

nt = ntcore.NetworkTableInstance.getDefault()
nt.setServer("127.0.0.1")
nt.startClient4("monnovis-api-server")

@app.route("/api/config/nt-team", methods=["POST"])
def nt_team():
    jData = flask.request.get_json(); 
    if (not jData): return "Bad Request Type", 400
    
    if (not "team" in jData): return "Bad Request Payload", 400
    team = int(jData["team"])
    try:
        nt.setServerTeam(team)
    except Exception as e:
        return repr(e), 400
    return "Team Number Successfully Set", 200

@app.route("/api/config/nt-addr", methods=["POST"])
def nt_addr():
    jData = flask.request.get_json(); 
    if (not jData): return "Bad Request Type", 400

    if (not "addr" in jData): return "Bad Request Payload", 400
    addr = jData["addr"]
    try:
        if ("port" in jData): 
            port = int(jData["port"])
            nt.setServer(addr, port)

            return f"NT Server Address Successfully Set to {addr}, Port set to {port}", 200
        else:
            nt.setServer(addr)
    
            return f"NT Server Address Successfully Set to {addr}, Using Default Port", 200
    except Exception as e:
        return repr(e), 400


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

nt_robotPosRePub: ntcore.StructPublisher = nt.getTable("Vision").getStructTopic("Robot_Pose", Pose2d).publish()
nt_simPosePub: ntcore.StructPublisher = nt.getTable("Vision").getStructTopic("Sim_Pose", Pose2d).publish()
nt_xPercentErrPub: ntcore.StructPublisher = nt.getTable("Vision").getDoubleTopic("xPercentErr").publish()
nt_yPercentErrPub: ntcore.StructPublisher = nt.getTable("Vision").getDoubleTopic("yPercentErr").publish()
nt_rPercentErrPub: ntcore.StructPublisher = nt.getTable("Vision").getDoubleTopic("rPercentErr").publish()
nt_tPercentErrPub: ntcore.StructPublisher = nt.getTable("Vision").getDoubleTopic("totalPercentErr").publish()

sim_pose = {"x": 0, "y": 0, "r": 0}
@app.route("/api/simulation-pose", methods=["GET", "PUT"])
def simulation_pose():
    if flask.request.method == "GET":
        nt_simPosePub.set(Pose2d(wpimath.units.meters(sim_pose["x"]), wpimath.units.meters(sim_pose["y"]), 
                    Rotation2d.fromDegrees(wpimath.units.degrees(sim_pose["r"]))))
        nt_robotPosRePub.set(Pose2d(wpimath.units.meters(robotPos_x.get()), 
                                    wpimath.units.meters(robotPos_y.get()), 
                                    Rotation2d.fromDegrees(wpimath.units.degrees(robotPos_r.get()))
                            ))
        return sim_pose, 200; 
    elif flask.request.method == "PUT":
        try:
            j = flask.request.get_json(cache=False)
            if ("x" in j and "y" in j and "r" in j):
                sim_pose["x"] = float(j["x"])
                sim_pose["y"] = float(j["y"])
                sim_pose["r"] = float(j["r"])

                x_perror = abs((robotPos_x.get() - sim_pose["x"]))
                nt_xPercentErrPub.set(x_perror)
                y_perror = abs((robotPos_y.get() - sim_pose["y"]))
                nt_yPercentErrPub.set(y_perror)
                r_perror = abs((robotPos_r.get() - sim_pose["r"]))
                nt_rPercentErrPub.set(r_perror)

                total_perror = x_perror + y_perror + r_perror
                nt_tPercentErrPub.set(total_perror)

                nt_simPosePub.set(Pose2d(wpimath.units.meters(sim_pose["x"]), wpimath.units.meters(sim_pose["y"]), 
                    Rotation2d.fromDegrees(wpimath.units.degrees(sim_pose["r"]))))
                nt_robotPosRePub.set(Pose2d(wpimath.units.meters(robotPos_x.get()), 
                                            wpimath.units.meters(robotPos_y.get()), 
                                            Rotation2d.fromDegrees(wpimath.units.degrees(robotPos_r.get()))
                                    )
                ) # republish robot pose in Pose2d for advantage scope
                return "Suscess", 200
        except:
            pass    
        return "Invalid Content", 400
    else: return "Bad Request", 400


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

sim_data = {
    "currentTick": -1,
    "resultTick": -1,
    "targetID": 0,
    "visionLocked": False,
    "visionLastTS": 0,
    "visionLastUpdateTime": 0,
    "reset": True, # True

    "forward": 0,
    "strafe": 0, 
    "rotation": 0,

    "xOff": 0,
    "yOff" : 0,
    "rOff": 0,
    "robotYaw": 0,
}

@app.route("/api/sim/tick_update", methods=["GET"])
def sim_tick_update():
    return {
        "tick_id": sim_data["currentTick"],
        "reset": sim_data["reset"], 
        "forward": sim_data["forward"],
        "strafe": sim_data["strafe"],
        "rotation": sim_data["rotation"],
    }

@app.route("/api/sim/tick_result", methods=["POST"])
def sim_tick_result():
    json = flask.request.json
    
    tick = int(json["tick_id"])
    if (tick != sim_data["currentTick"]):
        print( sim_data["currentTick"])
        print(f"Out of Order Tick, id: {json["tick_id"]}")
        return "tick OfO", 400
    sim_data["resultTick"] = tick
    sim_data["xOff"] = float(json["xOff"])
    sim_data["yOff"] = float(json["yOff"])    
    sim_data["rOff"] = float(json["rOff"])
    sim_data["robotYaw"] = float(json["robotYaw"])
    return "Suscess", 200

@app.route("/api/sim/reset_finish", methods=["POST"])
def sim_reset_check():
    json = flask.request.json
    if (int(json["tick_id"]) != sim_data["currentTick"]):
        print(f"Out of Order Tick, id: {json["tick_id"]}")
        return "tick OfO", 400
    sim_data["targetID"] = int(json["targetID"])
    sim_data["reset"] = False
    sim_data["visionLocked"] = False
    return "Suscess", 200

nt_camera_unity = nt.getTable("Vision").getSubTable("Cameras").getSubTable("Unity")
nt_camera_unity_corners = nt_camera_unity.getDoubleArrayTopic("corners").subscribe([])
nt_camera_unity_ids = nt_camera_unity.getIntegerArrayTopic("ids").subscribe([])
nt_camera_unity_ts = nt_camera_unity.getIntegerTopic("ts").subscribe(0)
@app.route("/api/sim/get_state", methods=["POST"])
def sim_get_current_state():
    if sim_data["reset"] == True:
        return "still resetting", 404

    json = flask.request.json
    if (int(json["tick_id"]) != sim_data["currentTick"]):
        print(f"Out of Order Tick, id: {json["tick_id"]}")
        return "tick OfO", 400

    current_corners_array = nt_camera_unity_corners.get()
    current_ids_array = nt_camera_unity_ids.get()


    if not sim_data["targetID"] in current_ids_array:
        return "locking nvever established", 404 # never established locking
    cornerBeginIdx = current_ids_array.index(sim_data["targetID"]) * 8


    out_of_bounds = False
    lastUpdatedTs = nt_camera_unity_ts.get()
    print(lastUpdatedTs)
    # new tag data
    if lastUpdatedTs != sim_data["visionLastTS"]:
        sim_data["visionLastTS"] = lastUpdatedTs
        sim_data["visionLastUpdateTime"] = time.time()
        sim_data["visionLocked"] = True
    # no new tag update, check if we timed out and is out of bounds
    elif ((time.time() - sim_data["visionLastUpdateTime"]) > 0.5): # half sec timeout
        if sim_data["visionLocked"] == False:
            return "lock not yet availiable", 404 # if the detector haven't catched up to reset
        else:
            out_of_bounds = True # if locked and lost locking, then we are out of bounds

    return {
        "out_of_bounds": out_of_bounds,
        "corners": current_corners_array[cornerBeginIdx:cornerBeginIdx+8],
        "xOff": sim_data["xOff"],
        "yOff": sim_data["yOff"],
        "rOff": sim_data["rOff"],
        "robot_yaw": sim_data['robotYaw']
    }

@app.route("/api/sim/reset", methods=["GET"])
def sim_reset():
    sim_data["reset"] = True
    sim_data["currentTick"] += 1

    return {
        "tick_id": sim_data["currentTick"]
    }

@app.route("/api/sim/try_action", methods=["POST"])
def sim_try_action():
    json = flask.request.json

    if (sim_data["reset"]): return "still resetting", 400
    if (sim_data["resultTick"] != sim_data["currentTick"]):
        return "last tick not yet processed", 404

    sim_data["currentTick"] += 1

    sim_data["forward"] = float(json["forward"])
    sim_data["strafe"] = float(json["strafe"])
    sim_data["rotation"] = float(json["rotation"])

    return {
        "tick_id": sim_data["currentTick"]
    }