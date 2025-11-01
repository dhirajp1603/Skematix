import React, { useState, useRef } from 'react'
// Import images from assets so Vite will bundle/serve them reliably
import img2d from './assets/placeholder-2D.jpg'
import img3d from './assets/placeholder-3D.png'

export default function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  // cache-bust key to force reload of updated asset files (set once per session)
  const [imgKey] = useState(() => Date.now())
  const fileInputRef = useRef(null)

  const navButtonBase = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: 40,
    padding: '8px 18px',
    borderRadius: 8,
    fontSize: 15,
    letterSpacing: 0.8,
    cursor: 'pointer',
    boxSizing: 'border-box',
  }

  const handleUploadClick = () => fileInputRef.current?.click()

  const handleFileChange = async (e) => {
    if (!e.target.files || e.target.files.length === 0) return
    const f = e.target.files[0]
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setLoading(true)

    const formData = new FormData()
    formData.append('file', f)

    try {
      await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      })
    } catch (err) {
      alert('Upload failed: ' + err)
    }
    setLoading(false)
  }

  return (
    <div
      style={{
        fontFamily: 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
        background: 'linear-gradient(120deg,#1b2231 0%,#233656 100%)',
        color: '#f1f6fc',
        minHeight: '100vh',
        boxSizing: 'border-box',
      }}
    >
      <nav
        style={{
          width: '100%',
          padding: '12px 3vw',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-start',
          background: '#151f33',
          borderBottom: '1px solid #47ffe3',
          position: 'sticky',
          top: 0,
          zIndex: 5,
        }}
      >
        <div style={{ fontSize: 28, fontWeight: 700, color: '#47ffe3', letterSpacing: '1px' }}>
          Skematix
        </div>
      </nav>

      <div className="page-wrapper">
        <section style={{ textAlign: 'center', padding: '72px 0 32px 0' }}>
          <h1
            style={{
              fontSize: '3rem',
              color: '#fff',
              fontWeight: 800,
              letterSpacing: '2px',
              marginBottom: 12,
            }}
          >
            Transform 2D Blueprints into Stunning 3D Models
          </h1>
          <p style={{ fontSize: 22, color: '#88feee', maxWidth: 800, margin: '0 auto' }}>
            Instantly visualize your designs. Drag-n-drop your blueprint, explore in 3D, and
            accelerate your project workflow—no CAD skills needed.
          </p>
        </section>

        

        <section className="centered-section" style={{ margin: '80px 0' }}>
          <div
            className="feature-input"
            style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}
          >
            <button className="cta-button" onClick={handleUploadClick}>
              Upload Blueprint
            </button>
          </div>

          <h2 style={{ fontSize: 30, color: '#47ffe3', marginBottom: 14 }}>What is 2D to 3D Conversion?</h2>
          <p style={{ color: '#f1f6fc', fontSize: 20, lineHeight: 1.6 }}>
            It's the process of transforming traditional 2D drawings or blueprints into photorealistic
            3D models. This unlocks true spatial understanding, easy walk-throughs, and realistic
            visualization—bringing ideas and plans to life before construction.
          </p>
        </section>

        <section className="how-works" style={{ margin: '80px 0', textAlign: 'left' }}>
          <h2 style={{ fontSize: 30, color: '#47ffe3', marginBottom: 14 }}>How Skematix Works</h2>
          <div className="how-works-container">
            <div className="how-left">
                <div className="how-cards">
                  <div className="how-card how-card-top">
                    <h3>1. Upload</h3>
                    <p>Choose your 2D blueprint image. Supported: JPG, PNG, JPEG.</p>
                  </div>
                  <div className="how-row">
                    <div className="how-card">
                      <h3>2. AI Conversion</h3>
                      <p>AI detects walls/rooms and generates a 3D mesh.</p>
                    </div>
                    <div className="how-card">
                      <h3>3. Explore</h3>
                      <p>View, orbit, and walk through your new space in 3D!</p>
                    </div>
                  </div>
                </div>
            </div>

            <div className="how-right">
              <div className="image-box">
                <div className="image-row">
                  <div className="image-item">
                    <div className="image-label">2D</div>
                    {/* append a stable cache-bust query so replacing the file in src/assets shows immediately */}
                    <img src={`${img2d}?t=${imgKey}`} alt="2D" />
                  </div>

                  <div className="arrow" aria-hidden>
                    {/* right-pointing arrow between images */}
                    <svg width="56" height="28" viewBox="0 0 56 28" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 14 H44 M36 6 L44 14 L36 22" stroke="#47ffe3" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>

                  <div className="image-item">
                    <div className="image-label">3D</div>
                    <img src={img3d} alt="3D" />
                  </div>
                </div>
              </div>
              
            </div>
          </div>
        </section>

        <section
          className="centered-section"
          style={{
            margin: '80px 0',
            background: 'rgba(71,255,227,0.1)',
            borderRadius: 20,
            padding: '48px 32px',
          }}
        >
          <h2 style={{ fontSize: 30, color: '#47ffe3', marginBottom: 14 }}>Why Choose Skematix?</h2>
          <ul
            style={{
              color: '#fff',
              fontSize: 20,
              lineHeight: 1.7,
              listStyleType: 'square',
              paddingLeft: 25,
              display: 'inline-block',
              textAlign: 'left',
            }}
          >
            <li>Automated, high-quality 2D-to-3D model conversion</li>
            <li>No engineering or expert CAD skills required</li>
            <li>Instant, browser-based exploration of real 3D spaces</li>
            <li>Fast, seamless project workflow and sharing</li>
          </ul>
        </section>

        

        <section
          style={{
            margin: '90px 0 40px 0',
            background: '#151f33',
            borderRadius: 25,
            boxShadow: '0 0 60px #0ff3e4a6',
            textAlign: 'center',
            padding: '52px 30px',
          }}
        >
          <h2 style={{ fontSize: 33, color: '#fff', fontWeight: 700, marginBottom: 16 }}>
            Get Started Now
          </h2>
          <p style={{ color: '#ddd', fontSize: 18, marginBottom: 30 }}>
            Upload your blueprint and experience a new dimension of design.
          </p>
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button onClick={handleUploadClick} className="cta-button">
              Upload Blueprint
            </button>
          </div>
          {preview && (
            <div>
              <img src={preview} alt="Blueprint Preview" className="preview-img" />
            </div>
          )}
          {loading && (
            <p style={{ fontSize: 19, color: '#47ffe3', marginTop: 26 }}>
              Processing your blueprint, please wait...
            </p>
          )}
        </section>
      </div>

      <footer
        style={{
          width: '100%',
          background: '#151f33',
          textAlign: 'center',
          color: '#47ffe3',
          padding: 26,
          fontSize: 14,
          marginTop: '70px',
        }}
      >
        © 2025 Skematix — Built for next-gen architectural visualization
      </footer>
    </div>
  )
}
