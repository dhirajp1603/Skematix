# FLASK INTEGRATION GUIDE
## Connecting Blueprint Pipeline to Web Interface

---

## CURRENT STATE

**Flask Backend**: `backend/app.py`  
**Serves**: Old cutaway converter system  
**Status**: ✅ Production-ready for old architecture  

**New Pipeline**: `pipeline/orchestrator.py`  
**Status**: ⏳ Stages 1-4 complete, Stages 5-9 stubbed  
**Integration**: Not yet connected to Flask  

---

## INTEGRATION STRATEGY

### Step 1: Keep Old System Running

The existing Flask backend (`http://127.0.0.1:5000`) should continue serving the old Type-1 to Cutaway converter.

**No changes to**:
- `backend/app.py`
- `backend/image_processing.py`
- Existing routes: `/`, `/upload`, `/review`

---

### Step 2: Add New Semantic Pipeline Routes

Create new endpoints that use the semantic pipeline **without modifying old routes**.

#### New Endpoints

```
POST /api/v2/blueprint/analyze
└─ Input: Blueprint image (multipart/form-data)
└─ Output: Semantic analysis JSON + room detection results
└─ Uses: Stages 1-4

POST /api/v2/blueprint/process
└─ Input: Blueprint image (multipart/form-data)
└─ Output: Complete 3D GLB model + analysis
└─ Uses: Stages 1-9 (when all complete)

GET /api/v2/blueprint/models/{model_id}
└─ Fetch generated GLB file for download
```

---

## IMPLEMENTATION

### Option A: Create New Flask Blueprint

**File**: `backend/semantic_routes.py`

```python
from flask import Blueprint, request, jsonify, send_file
from pipeline.orchestrator import BlueprintPipeline
import uuid
import os

semantic_bp = Blueprint('semantic', __name__, url_prefix='/api/v2/blueprint')

# Store models by ID for retrieval
GENERATED_MODELS = {}

@semantic_bp.route('/analyze', methods=['POST'])
def analyze_semantic():
    """
    Analyze blueprint and return semantic segmentation results
    
    Returns:
    {
        'status': 'success',
        'analysis': {
            'rooms': count,
            'walls': length_summary,
            'semantic_distribution': {
                'wall_pixels': 12345,
                'door_pixels': 456,
                'window_pixels': 789,
                'background_pixels': 98765
            }
        },
        'semantic_mask_url': 'image_url'
    }
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        # Save uploaded file
        upload_dir = 'uploads/blueprints'
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Run pipeline (stages 1-4 only)
        pipeline = BlueprintPipeline(filepath, device='cuda', verbose=True)
        success, message = pipeline.run_full_pipeline()
        
        if not success:
            return jsonify({
                'status': 'failed',
                'error': message,
                'details': pipeline.errors
            }), 400
        
        # Extract analysis results
        response = {
            'status': 'success',
            'analysis': {
                'rooms': len(pipeline.room_set.rooms) if pipeline.room_set else 0,
                'wall_length_px': sum(e.length_px for e in pipeline.wall_graph.edges.values()) if pipeline.wall_graph else 0,
                'semantic_distribution': {
                    'wall_pixels': int((pipeline.semantic_output.wall_mask > 0).sum()),
                    'door_pixels': int((pipeline.semantic_output.door_mask > 0).sum()),
                    'window_pixels': int((pipeline.semantic_output.window_mask > 0).sum()),
                    'background_pixels': int((pipeline.semantic_output.background_mask > 0).sum())
                }
            },
            'pipeline_summary': pipeline.get_summary()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@semantic_bp.route('/process', methods=['POST'])
def process_full():
    """
    Complete blueprint-to-3D processing pipeline
    
    Returns:
    {
        'status': 'success',
        'model_id': 'uuid',
        'model_url': '/api/v2/blueprint/models/uuid',
        'analysis': {
            'rooms': count,
            'walls': count,
            ...
        }
    }
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        # Save uploaded file
        upload_dir = 'uploads/blueprints'
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Run full pipeline (stages 1-9)
        output_dir = 'output/semantic_models'
        os.makedirs(output_dir, exist_ok=True)
        
        pipeline = BlueprintPipeline(filepath, device='cuda', verbose=True)
        success, message = pipeline.run_full_pipeline()
        
        if not success:
            return jsonify({
                'status': 'failed',
                'error': message,
                'details': pipeline.errors
            }), 400
        
        # Store model reference
        model_id = str(uuid.uuid4())
        GENERATED_MODELS[model_id] = {
            'glb_path': pipeline.glb_path,
            'source_image': filepath,
            'analysis': pipeline.get_summary()
        }
        
        response = {
            'status': 'success',
            'model_id': model_id,
            'model_url': f'/api/v2/blueprint/models/{model_id}',
            'analysis': {
                'rooms': len(pipeline.room_set.rooms) if pipeline.room_set else 0,
                'walls': len(pipeline.wall_graph.edges) if pipeline.wall_graph else 0,
                'junctions': len([v for v in (pipeline.wall_graph.vertices.values() if pipeline.wall_graph else []) if v.is_junction]),
                'scale': 'Real-world meters'
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@semantic_bp.route('/models/<model_id>', methods=['GET'])
def download_model(model_id):
    """Download generated GLB model"""
    if model_id not in GENERATED_MODELS:
        return jsonify({'error': 'Model not found'}), 404
    
    glb_path = GENERATED_MODELS[model_id]['glb_path']
    if not os.path.exists(glb_path):
        return jsonify({'error': 'GLB file not found'}), 404
    
    return send_file(glb_path, mimetype='model/gltf-binary', as_attachment=True)
```

### Update `backend/app.py`

```python
# Add to existing Flask app

from semantic_routes import semantic_bp

# Register new blueprint (doesn't affect old routes)
app.register_blueprint(semantic_bp)
```

---

## CLIENT INTEGRATION

### JavaScript/TypeScript Frontend

```javascript
// frontend/semantic-api.js

class BlueprintAnalyzer {
    constructor(baseUrl = '/api/v2/blueprint') {
        this.baseUrl = baseUrl;
    }

    async analyze(imageFile) {
        const formData = new FormData();
        formData.append('file', imageFile);

        const response = await fetch(`${this.baseUrl}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }

        return response.json();
    }

    async process(imageFile) {
        const formData = new FormData();
        formData.append('file', imageFile);

        const response = await fetch(`${this.baseUrl}/process`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }

        return response.json();
    }

    async downloadModel(modelId) {
        window.location.href = `${this.baseUrl}/models/${modelId}`;
    }
}

// Usage
const analyzer = new BlueprintAnalyzer();

// Step 1: Analyze
const input = document.getElementById('blueprint-input');
input.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const analysis = await analyzer.analyze(file);
    console.log('Rooms:', analysis.analysis.rooms);
    console.log('Distribution:', analysis.analysis.semantic_distribution);
});

// Step 2: Process full pipeline
const processBtn = document.getElementById('process-btn');
processBtn.addEventListener('click', async () => {
    const file = document.getElementById('blueprint-input').files[0];
    const result = await analyzer.process(file);
    console.log('Model ID:', result.model_id);
    console.log('Download:', result.model_url);
});
```

---

## API RESPONSE EXAMPLES

### `/analyze` Response

```json
{
    "status": "success",
    "analysis": {
        "rooms": 8,
        "wall_length_px": 15234,
        "semantic_distribution": {
            "wall_pixels": 123456,
            "door_pixels": 4567,
            "window_pixels": 8901,
            "background_pixels": 654321
        }
    },
    "pipeline_summary": {
        "success": true,
        "stages_completed": 4,
        "rooms_detected": 8,
        "output_path": "output/semantic_models/xyz/..."
    }
}
```

### `/process` Response

```json
{
    "status": "success",
    "model_id": "550e8400-e29b-41d4-a716-446655440000",
    "model_url": "/api/v2/blueprint/models/550e8400-e29b-41d4-a716-446655440000",
    "analysis": {
        "rooms": 8,
        "walls": 24,
        "junctions": 12,
        "scale": "Real-world meters"
    }
}
```

### Error Response

```json
{
    "status": "failed",
    "error": "Rooms merged at detection stage",
    "details": [
        "Room 1 and Room 2 share boundary pixels",
        "Recommendation: Check source image for ambiguous walls"
    ]
}
```

---

## DEPLOYMENT CHECKLIST

- [ ] Create `backend/semantic_routes.py`
- [ ] Update `backend/app.py` to register blueprint
- [ ] Create upload directory structure
- [ ] Test `/api/v2/blueprint/analyze` endpoint
- [ ] Test `/api/v2/blueprint/process` endpoint (stages 5-9 must be implemented first)
- [ ] Create frontend UI for semantic analysis
- [ ] Create 3D viewer for GLB models
- [ ] Add error handling for edge cases
- [ ] Document API endpoints
- [ ] Performance test with various blueprint sizes

---

## PERFORMANCE CONSIDERATIONS

| Task | Time | Optimization |
|------|------|--------------|
| Upload + save | <1s | Nginx buffering |
| Stage 1 (semantic) | 2-5s | GPU acceleration |
| Stages 2-4 (refinement) | 2-5s | CPU parallel |
| Stages 5-9 (geometry) | 5-10s | Blender GPU |
| **Total** | **15-25s** | Async task queue |

**Recommendation**: Use Celery for long-running tasks
```python
# backend/tasks.py
from celery import Celery

celery = Celery(app.name, broker='redis://localhost')

@celery.task
def process_blueprint_async(image_path):
    pipeline = BlueprintPipeline(image_path)
    return pipeline.run_full_pipeline()

# In route:
task = process_blueprint_async.delay(filepath)
# Return task ID to client for polling
```

---

## SUMMARY

**Old System** (still running):
- Routes: `/`, `/upload`, `/review`
- Purpose: Type-1 to Cutaway converter
- Status: ✅ Production

**New System** (being added):
- Routes: `/api/v2/blueprint/*`
- Purpose: Semantic blueprint analysis
- Status: ⏳ Integration ready (after stages 5-9 complete)

**No conflicts** - systems run in parallel on same Flask instance.

---
