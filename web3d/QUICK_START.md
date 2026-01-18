# Quick Start - 3D Floor Plan Web Viewer

**Get up and running in 2 minutes.**

---

## Step 1: Start a Web Server

Choose ONE option below:

### Option A: Node.js (Recommended)
```bash
# Install (one-time only)
npm install -g http-server

# Run
cd Skematix/web3d
http-server -p 8080 -g
```

### Option B: Python
```bash
cd Skematix/web3d
python -m http.server 8000
```

### Option C: VS Code
1. Install "Live Server" extension
2. Right-click `index.html` → "Open with Live Server"

---

## Step 2: Open Browser

Visit one of these URLs (depending on your server):

- **Node.js:** `http://localhost:8080`
- **Python:** `http://localhost:8000`
- **VS Code:** Automatically opens

---

## Step 3: View Your Floor Plan

✅ You should see a 3D rendered floor plan in your browser  
✅ The walls should be blue with proper shading  
✅ You can rotate, zoom, and pan

---

## Load Different Images

### Method 1: URL Parameter (Easy)
```
http://localhost:8080?image=output/image1_walls_mask_final.png
http://localhost:8080?image=output/image2_walls_mask_final.png
```

### Method 2: Edit index.html
Find this line in `index.html`:
```javascript
const imageSource = params.get('image') || 'output/test_plan_walls_mask_final.png';
```

Change to your image:
```javascript
const imageSource = 'output/your_image_walls_mask_final.png';
```

---

## Camera Controls

| Action | How |
|--------|-----|
| **Rotate** | Click and drag |
| **Zoom** | Scroll wheel |
| **Pan** | Right-click + drag |
| **Presets** | Click buttons on right panel |

---

## Troubleshooting

### Blank screen?
1. Open DevTools (F12)
2. Check console for errors
3. Verify image file exists
4. Make sure you're using a web server (not file://)

### Image not loading?
- Make sure image path is correct
- Check browser console for errors
- Verify image is a PNG file
- Confirm image is in the right directory

### Walls look dark?
- This is normal - it's 3D lighting
- Click camera preset buttons to change view
- Lighting adjusts based on camera angle

### Nothing happens?
- Check browser console (F12)
- Make sure web server is running
- Try a different browser

---

## File Structure

```
web3d/
├── index.html              ← Open this in browser
├── main.js                 ← Three.js scene setup
├── geometry-generator.js   ← Image to 3D conversion
└── README.md              ← Full documentation
```

---

## What's Happening?

1. **index.html** loads in browser
2. **main.js** initializes Three.js scene
3. **geometry-generator.js** loads your image
4. Wall pixels are detected (white = 255 RGB)
5. Walls are extruded to 3D
6. Three.js renders it in real-time

---

## Customization

### Change Wall Color
In `main.js`, find:
```javascript
wallColor: 0x4a9eff  // Blue
```
Change to:
```javascript
wallColor: 0xff6b6b  // Red
wallColor: 0x51cf66  // Green
wallColor: 0xffd700  // Gold
```

### Change Wall Height
In `geometry-generator.js`, find:
```javascript
wallHeight: 2.5  // meters
```
Change to `3.5` or `4.0` for taller walls.

### Change Background
In `main.js`, find:
```javascript
backgroundColor: 0x1a1a2e  // Dark blue
```
Change to any hex color.

---

## Next Steps

✅ Viewer is working? Great!  
📖 Want to customize? Read [README.md](README.md)  
🐛 Having issues? Check the troubleshooting section  
💾 Want to use your own images? Update the image path  

---

**That's it!** Your 3D floor plan viewer is running.

No Blender. No GLB files. No downloads. Just live, interactive 3D in your browser.
