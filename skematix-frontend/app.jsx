import React, { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';

export default function App() {
  const [modelUrl, setModelUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setModelUrl(data.model_url);
    } catch (err) {
      alert('Upload failed: ' + err.message);
    }
    setLoading(false);
  };

  // Simple 3D Viewer for GLB model
  function Model() {
    const { useGLTF } = require('@react-three/drei');
    const gltf = useGLTF(modelUrl);
    return <primitive object={gltf.scene} scale={1} />;
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Skematix - Upload 2D Blueprint</h1>
      <input type="file" onChange={handleUpload} accept="image/*" />
      {loading && <p>Processing blueprint...</p>}
      {modelUrl && (
        <Canvas style={{ height: '500px', width: '100%' }}>
          <ambientLight />
          <pointLight position={[10, 10, 10]} />
          <Model />
          <OrbitControls />
          <Environment background />
        </Canvas>
      )}
    </div>
  );
}
