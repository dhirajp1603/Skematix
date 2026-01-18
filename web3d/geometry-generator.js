/**
 * FLOOR PLAN GEOMETRY GENERATOR
 * 
 * Converts binary wall masks into Three.js geometries.
 * 
 * Process:
 * 1. Load image data from canvas
 * 2. Extract wall pixels (white = 255)
 * 3. Detect wall thickness and centerlines
 * 4. Create wall polygons
 * 5. Extrude to 3D using THREE.ExtrudeGeometry
 * 
 * Input: Binary mask image (white=walls, black=background)
 * Output: THREE.BufferGeometry ready for rendering
 */

import * as THREE from 'three';

export class FloorPlanGeometryGenerator {
    constructor(imageSource, options = {}) {
        this.imageSource = imageSource;
        this.options = {
            wallHeight: options.wallHeight || 2.5,      // meters
            scale: options.scale || 0.01,                // pixels to meters
            wallThickness: options.wallThickness || 0.2, // meters
            subdivisions: options.subdivisions || 2,     // geometry subdivisions
            ...options
        };
        
        this.imageData = null;
        this.width = 0;
        this.height = 0;
        this.wallPixels = null;
    }

    /**
     * Load image and prepare pixel data
     */
    async loadImage() {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                
                this.imageData = ctx.getImageData(0, 0, img.width, img.height);
                this.width = img.width;
                this.height = img.height;
                this.wallPixels = this._extractWallPixels();
                
                console.log(`[GeometryGenerator] Loaded image: ${this.width}x${this.height}`);
                console.log(`[GeometryGenerator] Wall pixels detected: ${this.wallPixels.size}`);
                
                resolve();
            };
            
            img.onerror = () => reject(new Error(`Failed to load image: ${this.imageSource}`));
            img.src = this.imageSource;
        });
    }

    /**
     * Extract white pixels (walls) from image
     */
    _extractWallPixels() {
        const pixels = new Set();
        const data = this.imageData.data;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const a = data[i + 3];
            
            // White pixel (wall)
            if (r > 200 && g > 200 && b > 200 && a > 200) {
                const pixelIndex = i / 4;
                pixels.add(pixelIndex);
            }
        }
        
        return pixels;
    }

    /**
     * Get pixel at coordinates
     */
    _getPixel(x, y) {
        if (x < 0 || x >= this.width || y < 0 || y >= this.height) return false;
        const idx = y * this.width + x;
        return this.wallPixels.has(idx);
    }

    /**
     * Trace contours of wall regions using edge detection
     */
    _extractWallContours() {
        const contours = [];
        const visited = new Set();
        
        // For each wall pixel, check if it's on a boundary
        for (const idx of this.wallPixels) {
            if (visited.has(idx)) continue;
            
            const x = idx % this.width;
            const y = Math.floor(idx / this.width);
            
            // Check if this pixel is on the edge of a wall region
            const isEdge = !this._getPixel(x - 1, y) || !this._getPixel(x + 1, y) ||
                          !this._getPixel(x, y - 1) || !this._getPixel(x, y + 1);
            
            if (isEdge && !visited.has(idx)) {
                // Trace this contour
                const contour = this._traceContour(x, y, visited);
                if (contour.length > 4) {
                    contours.push(contour);
                }
            }
        }
        
        return contours;
    }

    /**
     * Trace a single contour boundary
     */
    _traceContour(startX, startY, visited) {
        const contour = [];
        let x = startX;
        let y = startY;
        let direction = 0; // 0=right, 1=down, 2=left, 3=up
        
        const maxSteps = this.width * this.height;
        let steps = 0;
        
        do {
            contour.push([x, y]);
            visited.add(y * this.width + x);
            
            // Try to continue in current direction
            const [dx, dy] = [[1, 0], [0, 1], [-1, 0], [0, -1]][direction];
            let nextX = x + dx;
            let nextY = y + dy;
            
            if (this._getPixel(nextX, nextY)) {
                x = nextX;
                y = nextY;
            } else {
                // Try turning right
                direction = (direction + 1) % 4;
                const [dx2, dy2] = [[1, 0], [0, 1], [-1, 0], [0, -1]][direction];
                x = x + dx2;
                y = y + dy2;
            }
            
            steps++;
        } while (steps < maxSteps && !(x === startX && y === startY));
        
        return contour;
    }

    /**
     * Create wall polygons from contours
     */
    _createWallShapes() {
        const contours = this._extractWallContours();
        const shapes = [];
        
        // Group contours into outer walls and inner walls (doors/windows)
        const walls = this._groupContours(contours);
        
        for (const wall of walls) {
            try {
                const shape = new THREE.Shape();
                const points = wall.map(p => new THREE.Vector2(p[0], p[1]));
                
                if (points.length > 2) {
                    shape.setFromPoints(points);
                    shapes.push(shape);
                }
            } catch (e) {
                console.warn('[GeometryGenerator] Could not create shape:', e);
            }
        }
        
        console.log(`[GeometryGenerator] Created ${shapes.length} wall shapes`);
        return shapes;
    }

    /**
     * Group contours by size (walls vs openings)
     */
    _groupContours(contours) {
        // Sort by area
        const sortedContours = contours.sort((a, b) => {
            const areaA = this._calculateArea(a);
            const areaB = this._calculateArea(b);
            return areaB - areaA; // Largest first
        });
        
        return sortedContours;
    }

    /**
     * Calculate area of polygon
     */
    _calculateArea(points) {
        let area = 0;
        for (let i = 0; i < points.length; i++) {
            const p1 = points[i];
            const p2 = points[(i + 1) % points.length];
            area += (p2[0] - p1[0]) * (p2[1] + p1[1]);
        }
        return Math.abs(area) / 2;
    }

    /**
     * Generate THREE.BufferGeometry from wall shapes
     */
    generateGeometry() {
        const shapes = this._createWallShapes();
        
        if (shapes.length === 0) {
            console.error('[GeometryGenerator] No valid shapes found');
            return null;
        }
        
        const geometries = [];
        
        for (const shape of shapes) {
            try {
                // Extrude shape to create 3D walls
                const geometry = new THREE.ExtrudeGeometry(shape, {
                    depth: this.options.wallHeight,
                    bevelEnabled: false,
                    steps: this.options.subdivisions
                });
                
                // Scale from pixels to meters
                geometry.scale(this.options.scale, this.options.scale, 1);
                
                // Center on origin
                geometry.center();
                
                // Compute normals for proper lighting
                geometry.computeVertexNormals();
                
                geometries.push(geometry);
            } catch (e) {
                console.warn('[GeometryGenerator] Could not extrude shape:', e);
            }
        }
        
        if (geometries.length === 0) {
            console.error('[GeometryGenerator] No geometries created');
            return null;
        }
        
        // Merge all geometries into single BufferGeometry
        console.log(`[GeometryGenerator] Merging ${geometries.length} geometries...`);
        return this._mergeGeometries(geometries);
    }

    /**
     * Merge multiple geometries into one
     */
    _mergeGeometries(geometries) {
        let mergedGeometry = new THREE.BufferGeometry();
        
        const positions = [];
        const normals = [];
        const indices = [];
        let indexOffset = 0;
        
        for (const geometry of geometries) {
            // Get position data
            const posAttr = geometry.getAttribute('position');
            const normAttr = geometry.getAttribute('normal');
            const idxAttr = geometry.getIndex();
            
            if (posAttr) {
                positions.push(...posAttr.array);
            }
            if (normAttr) {
                normals.push(...normAttr.array);
            }
            
            if (idxAttr) {
                for (let i = 0; i < idxAttr.count; i++) {
                    indices.push(idxAttr.getX(i) + indexOffset);
                }
                indexOffset += posAttr.count;
            } else {
                // No index, add sequential indices
                for (let i = 0; i < posAttr.count; i++) {
                    indices.push(indexOffset + i);
                }
                indexOffset += posAttr.count;
            }
        }
        
        // Set attributes
        mergedGeometry.setAttribute('position', new THREE.BufferAttribute(
            new Float32Array(positions), 3
        ));
        
        if (normals.length > 0) {
            mergedGeometry.setAttribute('normal', new THREE.BufferAttribute(
                new Float32Array(normals), 3
            ));
        }
        
        mergedGeometry.setIndex(new THREE.BufferAttribute(
            new Uint32Array(indices), 1
        ));
        
        console.log(`[GeometryGenerator] Merged geometry: ${positions.length / 3} vertices, ${indices.length / 3} triangles`);
        
        return mergedGeometry;
    }

    /**
     * Full pipeline: load image → generate geometry
     */
    async generate() {
        try {
            console.log('[GeometryGenerator] Starting generation...');
            await this.loadImage();
            const geometry = this.generateGeometry();
            console.log('[GeometryGenerator] Generation complete!');
            return geometry;
        } catch (error) {
            console.error('[GeometryGenerator] Error:', error);
            throw error;
        }
    }
}

export default FloorPlanGeometryGenerator;
