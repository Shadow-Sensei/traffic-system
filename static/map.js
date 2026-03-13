const canvas = document.getElementById("mapCanvas");
const img = document.getElementById("mapImage");
const ctx = canvas.getContext("2d");

const signals = {
1:{ x: 165, y: 140 },
2:{ x: 84, y: 196 },
3:{ x: 151, y: 349 },
4:{ x: 228, y: 284 },
5:{ x: 678, y: 142 },
6:{ x: 597, y: 199 },
7:{ x: 654, y: 349 },
8:{ x: 740, y: 285 },
};

const allowed = {
1:[6],
2:[6],
3:[6],
4:[],
5:[4],
6:[],
7:[4],
8:[4]
};

let path = [];

img.onload = function(){

canvas.width = img.width;
canvas.height = img.height;

drawSignals();

};

function drawSignals(){

ctx.clearRect(0,0,canvas.width,canvas.height);

ctx.font = "14px Arial"; 

for(let s in signals){

let p = signals[s];

ctx.beginPath();
ctx.arc(p.x,p.y,10,0,2*Math.PI);
ctx.fillStyle="red";
ctx.fill();

ctx.fillStyle="black";
ctx.fillText(s,p.x+12,p.y+4);

}

}

function showError(message){

document.getElementById("errorText").innerText = message;
document.getElementById("errorPopup").style.display = "block";

}

function retryRoute(){
document.getElementById("errorPopup").style.display = "none";

path = [];

drawSignals();

}

function clearRoute(){

path = [];

drawSignals();

}

function sendPacket(){

if(path.length === 0){
showEmptyError();
return;
}

let packet = "<" + path.join(",") + ">";

console.log("Sending Packet:", packet);

fetch("/send_path",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
route:path
})
})
.then(res => res.json())
.then(data=>{
console.log("Server response:", data);

path = [];
drawSignals();
});

}

function showEmptyError(){
showError("No route selected");
}

canvas.addEventListener("click", function(e){

let rect = canvas.getBoundingClientRect();

let x = e.clientX - rect.left;
let y = e.clientY - rect.top;

for(let s in signals){

let p = signals[s];

let dist = Math.sqrt((x-p.x)**2 + (y-p.y)**2);

if(dist < 15){

let signalId = Number(s);

console.log("Selected:", signalId);

if(path.length === 0){
path.push(signalId);
}
else{

let last = path[path.length-1];

if(allowed[last].includes(signalId)){
path.push(signalId);
}
else{
console.log("Invalid move:", last, "→", signalId);
showError("Invalid route selected");
return;
}

}

drawRoute();
break;
}

}

});

function drawRoute(){

drawSignals();

ctx.beginPath();

for(let i=0;i<path.length;i++){

let p = signals[path[i]];

if(i === 0){
ctx.moveTo(p.x,p.y);
}
else{
ctx.lineTo(p.x,p.y);
}

}

ctx.strokeStyle = "blue";
ctx.lineWidth = 3;
ctx.stroke();

}