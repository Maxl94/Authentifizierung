var longitude = document.getElementsByName("longitude");
var latitude = document.getElementsByName("latitude");
var error = document.getElementById("error");

function getLocation() {
    console.log("Searching location")
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/api/location", true);
    xhr.onload = function (e) {
    if (xhr.readyState === 4) {
        if (xhr.status === 200) {
            console.log(xhr.responseText);
            position = JSON.parse(xhr.responseText)
            showPosition(position)
        } else {
            console.error(xhr.statusText);
        }
    }
    };
    xhr.onerror = function (e) {
        console.error(xhr.statusText);
    };
    xhr.send(null);
}

function showPosition(position) {
    console.log("Latitude: " + position.latitude + 
                "Longitude: " + position.longitude);
    longitude[0].innerhtl = position.longitude
    latitude[0].value = position.latitude
}