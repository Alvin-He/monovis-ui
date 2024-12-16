

const API_LOC = `${window.location.protocol}//${window.location.hostname}:${Number(window.location.port)+1}`;

async function fetchRobotPos() {
    res = await fetch(`${API_LOC}/api/robot-pose`);

    if (!res.ok) return null

    json = await res.json();

    return new FRCPose2d(json["x"], json["y"], json["r"]);
}