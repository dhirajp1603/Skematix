import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF, Html, Stage } from '@react-three/drei'

function ModelScene() {
  const gltf = useGLTF('/models/model.glb')
  return <primitive object={gltf.scene} dispose={null} />
}

export default function ModelViewer() {
  return (
    <div style={{ width: '100%', maxWidth: 1000, margin: '24px auto' }}>
      <Canvas style={{ width: '100%', height: 480 }} camera={{ position: [0, 2, 6], fov: 50 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} />
        <Suspense fallback={<Html>Loading model...</Html>}>
          <Stage intensity={1} environment={null} shadows={false} adjustCamera>
            <ModelScene />
          </Stage>
        </Suspense>
        <OrbitControls enablePan enableZoom enableRotate />
      </Canvas>
    </div>
  )
}
