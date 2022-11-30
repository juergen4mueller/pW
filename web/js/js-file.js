
function updateText(text) {
    const tAussenAct = document.getElementById("tAussenAct");
    tAussenAct.innerHTML = text;
}

function startApp() {
    eel.startApp();
}

function stopApp() {
    eel.stopApp();
}

function setResolution(width, height) {
    eel.setResolution(width, height)
}

eel.expose(say_hello_js); // Expose this function to Python
function say_hello_js(x) {
    console.log("Hello from " + x);
}

eel.expose(set_Gps_values);
function set_Gps_values(_gps_lat, _gps_lon, _gps_v_kmh, _gps_dir) {
    const kompassnadel = document.getElementById("kompassnadel");
    kompassnadel.style.transform = `rotate(${_gps_dir}deg)`;
    const gps_dir = document.getElementById("gps_dir");
    gps_dir.innerHTML = _gps_dir;
    const gps_lat = document.getElementById("gps_lat");
    gps_lat.innerHTML = _gps_lat;
    const gps_lon = document.getElementById("gps_lon");
    gps_lon.innerHTML = _gps_lon;
    const gps_speed = document.getElementById("gps_speed");
    gps_speed.innerHTML = _gps_v_kmh;
}


say_hello_js("Javascript World!");
eel.say_hello_py("Javascript World!"); // Call a Python function