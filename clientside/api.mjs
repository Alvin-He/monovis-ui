

const API_LOC = `${window.location.protocol}//${window.location.hostname}:${Number(window.location.port)+1}`;

async function getRobotPos() {
    res = await fetch(`${API_LOC}/api/robot-pose`);

    if (!res.ok) return null

    json = await res.json();

    return new FRCPose2d(json["x"], json["y"], json["r"]);
}

async function postNTTeam(team) {
    res = await fetch(`${API_LOC}/api/config/nt-team`, {
        method: "POST", 
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({"team": team})
    }); 

    return [res.ok, await res.text()];
}

async function postNTAddrPort(addr, port) {
    res = await fetch(`${API_LOC}/api/config/nt-addr`, {
        method: "POST", 
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({"addr": addr, "port": port})
    }); 

    return [res.ok, await res.text()];
}
