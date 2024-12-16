function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

const fieldDims = {x: 1654, y: 821}; 

let field = document.getElementById("field");
let fieldRobot = document.getElementById("field-robot"); 
const fieldRobotMaxSideLength = fieldRobot.offsetHeight > fieldRobot.offsetWidth ? fieldRobot.offsetHeight : fieldRobot.offsetWidth; 
function updateRobotPos(frcPose2d) {
    let relativeRobotWidth = (fieldRobot.offsetWidth/field.offsetWidth)/2; 
    let relativeRobotHeight = (fieldRobot.offsetHeight/field.offsetHeight)/2;

    let relativeBrowserX = (frcPose2d.x / fieldDims.x) - relativeRobotWidth; 
    let relativeBrowserY = (frcPose2d.y / fieldDims.y) + relativeRobotHeight; 

    fieldRobot.style.left = `${relativeBrowserX*100}%`;
    fieldRobot.style.top = `${(1-relativeBrowserY)*100}%`;
    fieldRobot.style.rotate = `${-90 + frcPose2d.r}deg`; 

    console.log(fieldRobot.style.left, fieldRobot.style.top, fieldRobot.style.rotate);
}

// using field 
// using fieldRobot 
// using fieldRobotMaxSideLength
function resizeFieldToProportion() {
    field.style.height = null;
    field.style.width = null;
    
    // y axis limited -- height limited 
    if (field.offsetHeight < field.offsetWidth) {
        let h = field.offsetHeight - fieldRobotMaxSideLength;
        let w = h * (fieldDims.x/fieldDims.y); 
        field.style.height = `${h}px`;
        field.style.width = `${w}px`; 
    } 
    // x axis limited -- width limited 
    else {
        let w = field.offsetWidth - fieldRobotMaxSideLength; 
        let h = w * (fieldDims.y / fieldDims.x);
        field.style.height = `${h}px`;
        field.style.width = `${w}px`; 
    }
}
async function main() {
    resizeFieldToProportion();
    new ResizeObserver(resizeFieldToProportion).observe(document.body);
    
    updateRobotPos(new FrcPose2d(0, 0, 0))
    while (true) {

        newRobotPos = await fetchRobotPos(); 
        if (newRobotPos) updateRobotPos(newRobotPos);
        
        await sleep(20);
    }
}
window.addEventListener("load", main);
