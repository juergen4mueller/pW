
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

eel.expose(set_Kompass_value);
function set_Kompass_value(x) {
    const kompassnadel = document.getElementById("kompassnadel");
    console.log(typeof (x))
    console.log(x)
    kompassnadel.style.transform = `rotate(${x}deg)`;
    const gps_dir = document.getElementById("gps_dir");
    gps_dir.innerHTML = x;
}

say_hello_js("Javascript World!");
eel.say_hello_py("Javascript World!"); // Call a Python function