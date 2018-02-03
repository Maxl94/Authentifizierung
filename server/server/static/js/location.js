var longitude = document.getElementsByName("longitude");
var latitude = document.getElementsByName("latitude");
var error = document.getElementById("error");

function getLocation() {
    console.log("Searching location")
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else { 
        console.log("... failed")
        error.innerHTML = "Geolocation is not supported by this browser.";
    }
}

function showPosition(position) {
    console.log("Latitude: " + position.coords.latitude + 
                    "Longitude: " + position.coords.longitude);
    longitude.value = position.coords.longitude
    latitude.value = position.coords.latitude
}