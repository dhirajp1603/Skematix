import React, { useState, useRef } from "react";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Shared styles to keep buttons visually consistent across the navbar
  const navButtonBase: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    height: 40,
    padding: "8px 18px",
    borderRadius: 8,
    fontSize: 15,
    letterSpacing: 0.8,
    cursor: "pointer",
    boxSizing: "border-box",
  };

  const handleUploadClick = () => fileInputRef.current?.click();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setFile(file);
    setPreview(URL.createObjectURL(file));
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Example API call - replace with your actual backend URL if needed
      await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      // You can handle the server response here, e.g., show success message or do next steps
      // const data = await response.json();
      // Do something with data...

    } catch (err) {
      alert("Upload failed: " + err);
    }
    setLoading(false);
  };

  return (
    <div
      style={{
        fontFamily: "Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
        background: "linear-gradient(120deg,#1b2231 0%,#233656 100%)",
        color: "#f1f6fc",
        minHeight: "100vh",
        boxSizing: "border-box",
      }}
    >
      {/* Navbar */}
      <nav
        style={{
          width: "100%",
          padding: "12px 3vw",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#151f33",
          borderBottom: "1px solid #47ffe3",
          position: "sticky",
          top: 0,
          zIndex: 5,
        }}
      >
        {/* logo on the far left */}
        <div style={{ fontSize: 28, fontWeight: 700, color: "#47ffe3", letterSpacing: "1px" }}>
          Skematix
        </div>

       
          
      </nav>

      <div className="page-wrapper">
        {/* Introduction */}
        <section style={{ textAlign: "center", padding: "72px 0 32px 0" }}>
          <h1
            style={{
              fontSize: "3rem",
              color: "#fff",
              fontWeight: 800,
              letterSpacing: "2px",
              marginBottom: 12,
            }}
          >
            Transform 2D Blueprints into Stunning 3D Models
          </h1>
          <p style={{ fontSize: 22, color: "#88feee", maxWidth: 800, margin: "0 auto" }}>
            Instantly visualize your designs. Drag-n-drop your blueprint, explore in 3D, and accelerate your project workflow—no CAD skills needed.
          </p>
        </section>

        {/* What is 2D to 3D Conversion */}
        <section className="centered-section" style={{ margin: "80px 0" }}>
          {/* centered CTA above the section (matches bottom 'Get Started') */}
          <div
            className="feature-input"
            style={{ display: "flex", justifyContent: "center", marginBottom: 20 }}
          >
            <button className="cta-button" onClick={handleUploadClick}>
              Upload Blueprint
            </button>
          </div>

          <h2 style={{ fontSize: 30, color: "#47ffe3", marginBottom: 14 }}>What is 2D to 3D Conversion?</h2>
          <p style={{ color: "#f1f6fc", fontSize: 20, lineHeight: 1.6 }}>
            It's the process of transforming traditional 2D drawings or blueprints into photorealistic 3D models. This unlocks true spatial understanding, easy walk-throughs, and realistic visualization—bringing ideas and plans to life before construction.
          </p>
        </section>

        {/* Why choose Skematix */}
        <section
          className="centered-section"
          style={{
            margin: "80px 0",
            background: "rgba(71,255,227,0.1)",
            borderRadius: 20,
            padding: "48px 32px",
          }}
        >
          <h2 style={{ fontSize: 30, color: "#47ffe3", marginBottom: 14 }}>Why Choose Skematix?</h2>
          <ul
            style={{ color: "#fff", fontSize: 20, lineHeight: 1.7, listStyleType: "square", paddingLeft: 25, display: "inline-block", textAlign: "left" }}
          >
            <li>Automated, high-quality 2D-to-3D model conversion</li>
            <li>No engineering or expert CAD skills required</li>
            <li>Instant, browser-based exploration of real 3D spaces</li>
            <li>Fast, seamless project workflow and sharing</li>
          </ul>
        </section>

        {/* How it works */}
        <section style={{ margin: "80px 0", textAlign: "center" }}>
          <h2 style={{ fontSize: 30, color: "#47ffe3", marginBottom: 14 }}>How Skematix Works</h2>
          <div
            style={{
              maxWidth: 900,
              margin: "32px auto 0 auto",
              display: "flex",
              gap: 36,
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                flex: "1 1 180px",
                background: "#203251",
                color: "#47ffe3",
                borderRadius: 15,
                padding: 28,
                minWidth: 240,
                boxShadow: "0 4px 20px rgba(71,255,227,0.05)",
              }}
            >
              <h3>1. Upload</h3>
              <p style={{ color: "#fff", fontWeight: 400 }}>
                Choose your 2D blueprint image. Supported: JPG, PNG, SVG.
              </p>
            </div>
            <div
              style={{
                flex: "1 1 180px",
                background: "#203251",
                color: "#47ffe3",
                borderRadius: 15,
                padding: 28,
                minWidth: 240,
                boxShadow: "0 4px 20px rgba(71,255,227,0.05)",
              }}
            >
              <h3>2. AI Conversion</h3>
              <p style={{ color: "#fff", fontWeight: 400 }}>
                AI detects walls/rooms and generates a 3D mesh.
              </p>
            </div>
            <div
              style={{
                flex: "1 1 180px",
                background: "#203251",
                color: "#47ffe3",
                borderRadius: 15,
                padding: 28,
                minWidth: 240,
                boxShadow: "0 4px 20px rgba(71,255,227,0.05)",
              }}
            >
              <h3>3. Explore</h3>
              <p style={{ color: "#fff", fontWeight: 400 }}>
                View, orbit, and walk through your new space in 3D!
              </p>
            </div>
          </div>
        </section>

        {/* Technologies Used */}
        <section
          style={{
            margin: "80px 0",
          }}
        >
          <h2 style={{ fontSize: 30, color: "#47ffe3", marginBottom: 14 }}>
            Technologies powering Skematix
          </h2>
          <ul style={{ color: "#fff", fontSize: 20, lineHeight: 2, paddingLeft: 20, listStyle: "disc" }}>
            <li>React &amp; modern frontend technologies</li>
            <li>Computer Vision (OpenCV)</li>
            <li>3D Modeling (Blender & Python tooling)</li>
            <li>Backend with FastAPI and Cloud Deployment</li>
          </ul>
        </section>

        {/* Get Started */}
        <section
          style={{
            margin: "90px 0 40px 0",
            background: "#151f33",
            borderRadius: 25,
            boxShadow: "0 0 60px #0ff3e4a6",
            textAlign: "center",
            padding: "52px 30px",
          }}
        >
          <h2
            style={{ fontSize: 33, color: "#fff", fontWeight: 700, marginBottom: 16 }}
          >
            Get Started Now
          </h2>
          <p style={{ color: "#ddd", fontSize: 18, marginBottom: 30 }}>
            Upload your blueprint and experience a new dimension of design.
          </p>
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <div style={{ display: "flex", justifyContent: "center" }}>
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
            <p style={{ fontSize: 19, color: "#47ffe3", marginTop: 26 }}>
              Processing your blueprint, please wait...
            </p>
          )}
        </section>
      </div>

      {/* Footer */}
      <footer
        style={{
          width: "100%",
          background: "#151f33",
          textAlign: "center",
          color: "#47ffe3",
          padding: 26,
          fontSize: 14,
          marginTop: "70px",
        }}
      >
        © 2025 Skematix — Built for next-gen architectural visualization
      </footer>
    </div>
  );
}
