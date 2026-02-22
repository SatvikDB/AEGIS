// static/js/geo.js - Complete replacement with animated globe
// Handles GPS panel display + embedded animated globe

let _globeTimer = null;
let _globeRot   = 0;

function renderGeo(geoData) {
    console.log('renderGeo called with:', geoData);
    var panel = document.getElementById('geoPanel');
    console.log('geoPanel element:', panel);
    if (!panel) return;
    if (!geoData || !geoData.latitude) {
        console.log('No geo data or latitude, hiding panel');
        panel.classList.add('hidden');
        return;
    }
    console.log('Showing geo panel');
    panel.classList.remove('hidden');

    var latEl = document.getElementById('geoLat');
    var lonEl = document.getElementById('geoLon');
    var locEl = document.getElementById('geoLoc');
    var altEl = document.getElementById('geoAlt');
    var lnkEl = document.getElementById('geoMapLink');

    if (latEl) latEl.textContent =
        Math.abs(geoData.latitude).toFixed(4) + String.fromCharCode(176) +
        ' ' + (geoData.latitude >= 0 ? 'N' : 'S');
    if (lonEl) lonEl.textContent =
        Math.abs(geoData.longitude).toFixed(4) + String.fromCharCode(176) +
        ' ' + (geoData.longitude >= 0 ? 'E' : 'W');
    if (locEl) locEl.textContent = geoData.location_name || 'Coordinates acquired';
    if (altEl) altEl.textContent = geoData.altitude ? 'Altitude: ' + geoData.altitude + 'm ASL' : '';
    if (lnkEl) { lnkEl.href = geoData.maps_link; lnkEl.style.display = 'inline-flex'; }

    startGlobe(geoData.latitude, geoData.longitude);
}

function startGlobe(targetLat, targetLon) {
    var canvas = document.getElementById('aegisGlobe');
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext('2d');
    var W = 260, H = 260, R = 100, CX = 130, CY = 130;
    canvas.width = W; canvas.height = H;
    if (_globeTimer) clearInterval(_globeTimer);
    _globeRot = 0;

    var tlat = targetLat * Math.PI / 180;
    var tlon = targetLon * Math.PI / 180;

    function pt(latR, lonR) {
        var x = Math.cos(latR) * Math.sin(lonR + _globeRot);
        var y = Math.sin(latR);
        var z = Math.cos(latR) * Math.cos(lonR + _globeRot);
        return { x: CX + x * R, y: CY - y * R, v: z > 0 };
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = '#020906'; ctx.fillRect(0, 0, W, H);

        // Globe base gradient
        var bg = ctx.createRadialGradient(CX-30,CY-30,5,CX,CY,R);
        bg.addColorStop(0, '#0d2214');
        bg.addColorStop(0.6, '#071409');
        bg.addColorStop(1, '#020806');
        ctx.fillStyle = bg;
        ctx.beginPath(); ctx.arc(CX,CY,R,0,Math.PI*2); ctx.fill();

        // Clip to globe circle
        ctx.save();
        ctx.beginPath(); ctx.arc(CX,CY,R,0,Math.PI*2); ctx.clip();

        // Lat lines
        ctx.strokeStyle = 'rgba(0,255,82,0.07)'; ctx.lineWidth = 0.5;
        [-60,-30,0,30,60].forEach(function(latD) {
            var lr = latD * Math.PI / 180;
            ctx.beginPath(); var first = true;
            for (var ld = -180; ld <= 180; ld += 4) {
                var pp = pt(lr, ld * Math.PI / 180);
                if (pp.v) { first ? ctx.moveTo(pp.x,pp.y) : ctx.lineTo(pp.x,pp.y); first=false; }
            }
            ctx.stroke();
        });

        // Lon lines
        [-150,-120,-90,-60,-30,0,30,60,90,120,150,180].forEach(function(lonD) {
            var lr2 = lonD * Math.PI / 180;
            ctx.beginPath(); var first2 = true;
            for (var la = -90; la <= 90; la += 4) {
                var pp2 = pt(la * Math.PI / 180, lr2);
                if (pp2.v) { first2 ? ctx.moveTo(pp2.x,pp2.y) : ctx.lineTo(pp2.x,pp2.y); first2=false; }
            }
            ctx.stroke();
        });

        // Continent patches
        var conts = [
            [[37,-6],[32,18],[14,40],[4,42],[-17,35],[-34,0],[-18,-15],[15,-15],[34,-5]],
            [[0,36],[30,26],[60,37],[90,52],[120,55],[140,38],[130,30],[80,10],[45,38]],
            [[-70,5],[-85,12],[-100,28],[-120,36],[-150,70],[-140,52],[-120,36],[-88,15]],
            [[114,-22],[128,-16],[140,-18],[152,-24],[150,-35],[138,-36],[130,-32]],
        ];
        conts.forEach(function(pts) {
            ctx.beginPath(); var f2=true;
            pts.forEach(function(c) {
                var pp3 = pt(c[1]*Math.PI/180, c[0]*Math.PI/180);
                if (pp3.v) { f2 ? ctx.moveTo(pp3.x,pp3.y) : ctx.lineTo(pp3.x,pp3.y); f2=false; }
            });
            ctx.closePath();
            ctx.fillStyle='rgba(0,80,30,0.55)'; ctx.fill();
            ctx.strokeStyle='rgba(0,160,60,0.18)'; ctx.lineWidth=0.5; ctx.stroke();
        });

        ctx.restore();

        // Globe rim
        ctx.strokeStyle='rgba(0,255,82,0.3)'; ctx.lineWidth=1.5;
        ctx.beginPath(); ctx.arc(CX,CY,R,0,Math.PI*2); ctx.stroke();

        // Specular highlight
        var sp2 = ctx.createRadialGradient(CX-35,CY-35,0,CX-20,CY-20,R*0.55);
        sp2.addColorStop(0,'rgba(200,255,220,0.07)'); sp2.addColorStop(1,'transparent');
        ctx.fillStyle=sp2; ctx.beginPath(); ctx.arc(CX,CY,R,0,Math.PI*2); ctx.fill();

        // Target location marker
        var mp = pt(tlat, tlon);
        if (mp.v) {
            var pulse = 6 + Math.sin(Date.now() * 0.005) * 3;
            ctx.strokeStyle='#ff2244'; ctx.lineWidth=1; ctx.globalAlpha=0.6;
            ctx.beginPath(); ctx.arc(mp.x,mp.y,pulse,0,Math.PI*2); ctx.stroke();
            ctx.globalAlpha=1;
            ctx.fillStyle='#ff2244'; ctx.shadowColor='#ff2244'; ctx.shadowBlur=10;
            ctx.beginPath(); ctx.arc(mp.x,mp.y,4,0,Math.PI*2); ctx.fill();
            ctx.shadowBlur=0;
            ctx.strokeStyle='rgba(255,34,68,0.7)'; ctx.lineWidth=1;
            ctx.beginPath();
            ctx.moveTo(mp.x-12,mp.y); ctx.lineTo(mp.x-6,mp.y);
            ctx.moveTo(mp.x+6,mp.y);  ctx.lineTo(mp.x+12,mp.y);
            ctx.moveTo(mp.x,mp.y-12); ctx.lineTo(mp.x,mp.y-6);
            ctx.moveTo(mp.x,mp.y+6);  ctx.lineTo(mp.x,mp.y+12);
            ctx.stroke();
        }

        _globeRot += 0.006;
    }

    _globeTimer = setInterval(draw, 33);
    draw();
}
