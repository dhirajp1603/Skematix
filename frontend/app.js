const API_BASE = 'http://localhost:5000';

const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const previewImg = document.getElementById('previewImg');
const overlay = document.getElementById('overlay');
const info = document.getElementById('info');
const saveEdits = document.getElementById('saveEdits');
const generate3d = document.getElementById('generate3d');
const scaleDisplay = document.getElementById('scaleDisplay');
const calibrateBtn = document.getElementById('calibrateScale');
const placeDoorBtn = document.getElementById('placeDoor');
const placeWindowBtn = document.getElementById('placeWindow');

let currentImageName = null;
let detected = null;
let mode = 'idle'; // 'idle'|'calibrate'|'door'|'window'|'draw'
let scale_m_per_px = null;
let calibratePts = [];
// per-image extras
let extras = { doors: [], windows: [], scale: null };

function setCanvasSize() {
  overlay.width = previewImg.clientWidth;
  overlay.height = previewImg.clientHeight;
}



uploadForm.addEventListener('submit', async (e)=>{
  e.preventDefault();
  if (!fileInput.files || fileInput.files.length===0) return alert('Select a file');
  const fd = new FormData(); fd.append('file', fileInput.files[0]);
  info.textContent = 'Uploading...';
  const res = await fetch(API_BASE + '/upload', {method:'POST', body:fd});
  if (!res.ok) { const t = await res.json().catch(()=>null); info.textContent = t && t.error ? t.error : 'Upload failed'; console.error(t); return; }
  const data = await res.json();
  currentImageName = data.filename || fileInput.files[0].name;
  // preview the uploaded file from backend input folder
  previewImg.src = API_BASE + '/input/' + currentImageName;
  // prepare detected walls and extras (doors/windows) from backend
  detected = data.walls || data; // flexible
  extras = extras || {doors:[], windows:[], scale:null};
  extras.doors = [];
  try{
    if (Array.isArray(detected)){
      detected.forEach(w=>{
        if (w && w.doors && Array.isArray(w.doors)){
          w.doors.forEach(d=>{ if (d && d.center) extras.doors.push({ pos: d.center }); });
        }
      });
    }
  }catch(e){ console.warn('no doors in response', e); }

  previewImg.onload = ()=>{ setCanvasSize();
    // compute px positions for detected doors/windows
    extras.doors.forEach(d=>{ d.px = [d.pos[0]*overlay.width, d.pos[1]*overlay.height]; });
    extras.windows = extras.windows || [];
    drawDetections(); };
  // if backend returned a scale, use it
  if (data.scale) {
    scale_m_per_px = data.scale;
    extras.scale = scale_m_per_px;
    scaleDisplay.textContent = (scale_m_per_px || '—');
  } else if (data.scale_m_per_px) {
    scale_m_per_px = data.scale_m_per_px;
    extras.scale = scale_m_per_px;
    scaleDisplay.textContent = (scale_m_per_px || '—');
  }
  info.textContent = 'Detected: ' + (Array.isArray(detected)? detected.length+' items' : JSON.stringify(detected).slice(0,120));
  saveEdits.disabled = false; generate3d.disabled = false;
  document.getElementById('jsonOut').textContent = JSON.stringify(detected,null,2);
});

window.addEventListener('resize', ()=>{ setCanvasSize(); drawDetections(); });

saveEdits.addEventListener('click', async ()=>{
  if (!currentImageName) return;
  const payload = { image: currentImageName, data: detected, extras: extras };
  const res = await fetch(API_BASE + '/detections/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  if (!res.ok) { alert('Save failed'); return; }
  alert('Saved corrections');
});

generate3d.addEventListener('click', async ()=>{
  if (!currentImageName) return;
  info.textContent = 'Generating 3D model... (this may take 1-2 minutes)';
  // Re-upload the same file name from input to trigger /upload, backend will run Blender if configured
  const res = await fetch(API_BASE + '/upload', {method:'POST', body: new FormData(document.getElementById('uploadForm'))});
  if (!res.ok) { info.textContent='3D generation failed'; const t=await res.json().catch(()=>null); console.error(t); return; }
  const d = await res.json();
  if (d.gltf) {
    info.textContent = '✓ 3D model generated! ';
    // Provide download link
    const link = document.createElement('a');
    link.href = API_BASE + '/' + d.gltf;
    link.download = d.gltf.split('/').pop();
    link.textContent = '📥 Download 3D Model (GLB)';
    link.style.display = 'inline-block';
    link.style.marginTop = '10px';
    link.style.padding = '10px 20px';
    link.style.backgroundColor = '#4CAF50';
    link.style.color = 'white';
    link.style.textDecoration = 'none';
    link.style.borderRadius = '4px';
    link.style.cursor = 'pointer';
    info.appendChild(document.createElement('br'));
    info.appendChild(link);
  } else {
    info.textContent = '⚠ 3D generation was not completed. Make sure Blender is installed and BLENDER_PATH environment variable is set.';
  }
});

// 3D Model Viewer using Three.js

// Simple draw on top to allow marking (not full-featured) — add points to a current polygon
let currentPoly = null;
overlay.addEventListener('click', (ev)=>{
  if (!previewImg.src) return;
  const rect = overlay.getBoundingClientRect();
  const x_px = (ev.clientX - rect.left);
  const y_px = (ev.clientY - rect.top);
  const x = x_px/overlay.width;
  const y = y_px/overlay.height;

  if (mode === 'calibrate') {
    calibratePts.push([x_px, y_px]);
    // draw a small marker
    const ctx = overlay.getContext('2d'); ctx.fillStyle='#22aa22'; ctx.beginPath(); ctx.arc(x_px, y_px, 6, 0, Math.PI*2); ctx.fill();
    if (calibratePts.length === 2) {
      const dx = calibratePts[0][0] - calibratePts[1][0];
      const dy = calibratePts[0][1] - calibratePts[1][1];
      const pxDist = Math.hypot(dx, dy);
      const meters = parseFloat(prompt('Enter real-world distance between the two points in meters (e.g. 2.0):'));
      if (!isNaN(meters) && meters > 0) {
        scale_m_per_px = meters / pxDist;
        extras.scale = scale_m_per_px;
        scaleDisplay.textContent = scale_m_per_px.toFixed(6);
        alert('Scale set: ' + scale_m_per_px + ' meters per pixel');
      } else {
        alert('Invalid distance entered. Calibration cancelled.');
      }
      mode = 'idle'; calibratePts = [];
    }
    return;
  }

  if (mode === 'door') {
    // add door marker (normalized coords)
    extras.doors.push({ pos: [x,y], px: [x_px, y_px] });
    drawDetections(); return;
  }

  if (mode === 'window') {
    extras.windows.push({ pos: [x,y], px: [x_px, y_px] });
    drawDetections(); return;
  }

  // default: drawing polygons (existing behavior)
  if (!currentPoly) { currentPoly = []; if (!Array.isArray(detected)) detected = []; detected.push(currentPoly); }
  currentPoly.push([x,y]); drawDetections();
});

// double-click to close current polygon
overlay.addEventListener('dblclick', ()=>{ currentPoly=null; document.getElementById('jsonOut').textContent = JSON.stringify(detected,null,2); });

// Mode button handlers
calibrateBtn.addEventListener('click', ()=>{
  mode = (mode === 'calibrate') ? 'idle' : 'calibrate';
  calibrateBtn.classList.toggle('modeActive', mode === 'calibrate');
  placeDoorBtn.classList.remove('modeActive'); placeWindowBtn.classList.remove('modeActive');
  calibratePts = [];
});
placeDoorBtn.addEventListener('click', ()=>{
  mode = (mode === 'door') ? 'idle' : 'door';
  placeDoorBtn.classList.toggle('modeActive', mode === 'door');
  placeWindowBtn.classList.remove('modeActive'); calibrateBtn.classList.remove('modeActive');
});
placeWindowBtn.addEventListener('click', ()=>{
  mode = (mode === 'window') ? 'idle' : 'window';
  placeWindowBtn.classList.toggle('modeActive', mode === 'window');
  placeDoorBtn.classList.remove('modeActive'); calibrateBtn.classList.remove('modeActive');
});

// Extend drawDetections to show doors/windows and scale markers
const origDraw = drawDetections;
function drawDetections(){
  const ctx = overlay.getContext('2d');
  ctx.clearRect(0,0,overlay.width,overlay.height);
  if (Array.isArray(detected)) {
    ctx.strokeStyle = 'rgba(200,20,20,0.9)'; ctx.lineWidth = 2;
    detected.forEach(item=>{
      // Handle both polygon arrays and wall objects with bbox/poly properties
      let poly = null;
      if (Array.isArray(item) && item.length > 0) {
        // Direct polygon array
        poly = item;
      } else if (item && typeof item === 'object') {
        // Wall object with poly or bbox
        if (item.poly && Array.isArray(item.poly)) {
          poly = item.poly;
        } else if (item.bbox) {
          // Draw bbox as rectangle
          const {x, y, w, h} = item.bbox;
          const imgW = previewImg.naturalWidth || 1;
          const imgH = previewImg.naturalHeight || 1;
          ctx.strokeStyle = 'rgba(200,20,20,0.9)';
          ctx.lineWidth = 2;
          ctx.strokeRect(x/imgW*overlay.width, y/imgH*overlay.height, w/imgW*overlay.width, h/imgH*overlay.height);
          return;
        }
      }
      
      if (poly && poly.length > 0) {
        ctx.beginPath();
        poly.forEach((pt,i)=>{ 
          const x = Array.isArray(pt) ? pt[0] : (typeof pt === 'object' ? pt.x : pt);
          const y = Array.isArray(pt) ? pt[1] : (typeof pt === 'object' ? pt.y : 0);
          const px = x < 1 ? x*overlay.width : x;
          const py = y < 1 ? y*overlay.height : y;
          if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py); 
        });
        ctx.closePath(); ctx.stroke();
      }
    });
  }
  // draw doors
  if (extras.doors){ ctx.fillStyle='#ff8800'; extras.doors.forEach(d=>{ const x=d.px[0], y=d.px[1]; ctx.fillRect(x-6,y-3,12,6); }); }
  // draw windows
  if (extras.windows){ ctx.fillStyle='#0099ff'; extras.windows.forEach(w=>{ const x=w.px[0], y=w.px[1]; ctx.fillRect(x-9,y-2,18,4); }); }
  // draw scale marker if exists
  if (scale_m_per_px){ ctx.fillStyle='#22aa22'; ctx.beginPath(); ctx.arc(12, overlay.height-12, 6, 0, Math.PI*2); ctx.fill(); ctx.fillStyle='black'; ctx.font='12px sans-serif'; ctx.fillText(scale_m_per_px.toFixed(4)+' m/px', 26, overlay.height-6); }
}

