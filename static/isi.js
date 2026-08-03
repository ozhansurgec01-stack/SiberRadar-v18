window.isiLayer=null;

window.isiAc=function(){

fetch('/api/temperature-map')
.then(r=>r.json())
.then(veri=>{

let noktalar=veri.map(x=>{

let t=x.sicaklik || 20;

let d=
t<10 ? 0.15 :
t<18 ? 0.30 :
t<25 ? 0.50 :
t<30 ? 0.70 :
t<35 ? 0.85 : 1;

return [x.lat,x.lng,d];

});


if(window.isiLayer){
    map.removeLayer(window.isiLayer);
}

window.isiLayer=L.heatLayer(noktalar,{
 radius:80,
 blur:60,
 minOpacity:0.45,
 gradient:{
 0.15:"#004cff",
 0.30:"#00ffff",
 0.50:"#00ff00",
 0.70:"#ffff00",
 0.85:"#ff6600",
 1:"#ff0000"
 }
}).addTo(map);


document.getElementById("isiBtn").innerText="🌡️ ISI (AÇIK)";

})
.catch(e=>console.log("ISI HATA",e));

}
