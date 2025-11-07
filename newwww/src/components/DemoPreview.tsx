import { motion } from "motion/react";
import { Play, Maximize2, RotateCw, ZoomIn, ArrowRight } from "lucide-react";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { useState } from "react";

export function DemoPreview() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleViewFullDemo = () => {
    setIsFullscreen(true);
  };

  return (
    <>
    <section className="py-24 bg-black relative overflow-hidden">
      {/* Blueprint Grid Background */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(47, 128, 237, 0.5) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(47, 128, 237, 0.5) 1px, transparent 1px)`,
          backgroundSize: '30px 30px'
        }} />
      </div>

      {/* Radial Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-radial from-[#2F80ED]/10 via-transparent to-transparent" />

      <div className="container mx-auto px-4 relative z-10">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl mb-4 text-white">
            Experience the Future of Design
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Watch your blueprints come to life in real-time with our interactive 3D viewer
          </p>
        </motion.div>

        <motion.div
          className="max-w-5xl mx-auto"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          {/* 3D Viewer Mockup */}
          <div className="relative rounded-lg border-2 border-[#2F80ED]/30 overflow-hidden bg-slate-900">
            {/* Viewer Controls */}
            <div className="flex items-center justify-between p-4 bg-slate-950 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <span className="ml-4 text-sm text-slate-400">3D Viewer - House_Plan_Final.pdf</span>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="ghost" className="text-slate-400 hover:text-[#2F80ED]">
                  <RotateCw className="w-4 h-4" />
                </Button>
                <Button size="sm" variant="ghost" className="text-slate-400 hover:text-[#2F80ED]">
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button size="sm" variant="ghost" className="text-slate-400 hover:text-[#2F80ED]">
                  <Maximize2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Viewer Content */}
            <div className="relative aspect-video bg-gradient-to-br from-slate-900 to-slate-950 flex items-center justify-center overflow-hidden">
              {/* 3D Grid Floor */}
              <svg className="absolute inset-0 w-full h-full opacity-30" viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg">
                {/* Perspective Grid */}
                <defs>
                  <pattern id="grid" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#2F80ED" strokeWidth="0.5" opacity="0.3"/>
                  </pattern>
                </defs>
                <rect width="800" height="450" fill="url(#grid)" />
              </svg>

              {/* 3D Wireframe House with Animation */}
              <motion.svg 
                className="relative z-10 w-3/4 h-3/4" 
                viewBox="0 0 400 300" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <motion.g 
                  transform="translate(200, 150)"
                  animate={{ rotateY: [0, 360] }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                >
                  {/* Base/Floor */}
                  <motion.path 
                    d="M -100 50 L 100 50 L 120 30 L -80 30 Z" 
                    fill="none" 
                    stroke="#2F80ED" 
                    strokeWidth="2" 
                    opacity="0.6"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.5 }}
                  />
                  
                  {/* Back Wall */}
                  <motion.path 
                    d="M -80 30 L 120 30 L 120 -50 L -80 -50 Z" 
                    fill="none" 
                    stroke="#2F80ED" 
                    strokeWidth="1.5" 
                    opacity="0.4"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.5, delay: 0.2 }}
                  />
                  
                  {/* Left Wall */}
                  <motion.path 
                    d="M -100 50 L -80 30 L -80 -50 L -100 -30 Z" 
                    fill="none" 
                    stroke="#2F80ED" 
                    strokeWidth="2" 
                    opacity="0.7"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.5, delay: 0.4 }}
                  />
                  
                  {/* Front Wall */}
                  <motion.path 
                    d="M -100 50 L 100 50 L 100 -30 L -100 -30 Z" 
                    fill="none" 
                    stroke="#2F80ED" 
                    strokeWidth="2.5" 
                    opacity="0.9"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.5, delay: 0.6 }}
                  />
                  
                  {/* Roof */}
                  <motion.path 
                    d="M -100 -30 L 0 -80 L 100 -30" 
                    fill="none" 
                    stroke="#2F80ED" 
                    strokeWidth="2" 
                    opacity="0.8"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 1.5, delay: 0.8 }}
                  />
                  <path d="M -80 -50 L 0 -90 L 120 -50" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.5" />
                  <line x1="0" y1="-80" x2="0" y2="-90" stroke="#2F80ED" strokeWidth="1.5" opacity="0.6" />
                  <line x1="-100" y1="-30" x2="-80" y2="-50" stroke="#2F80ED" strokeWidth="1.5" opacity="0.6" />
                  <line x1="100" y1="-30" x2="120" y2="-50" stroke="#2F80ED" strokeWidth="1.5" opacity="0.6" />
                  
                  {/* Door */}
                  <rect x="-10" y="10" width="20" height="40" fill="none" stroke="#2F80ED" strokeWidth="2" opacity="0.8" />
                  
                  {/* Windows */}
                  <rect x="-70" y="-10" width="25" height="25" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.7" />
                  <rect x="45" y="-10" width="25" height="25" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.7" />
                  
                  {/* Glowing Points */}
                  <circle cx="-100" cy="-30" r="2" fill="#2F80ED" opacity="0.9">
                    <animate attributeName="r" values="2;4;2" duration="2s" repeatCount="indefinite" />
                  </circle>
                  <circle cx="100" cy="-30" r="2" fill="#2F80ED" opacity="0.9">
                    <animate attributeName="r" values="2;4;2" duration="2s" begin="0.5s" repeatCount="indefinite" />
                  </circle>
                  <circle cx="0" cy="-80" r="2" fill="#2F80ED" opacity="0.9">
                    <animate attributeName="r" values="2;4;2" duration="2s" begin="1s" repeatCount="indefinite" />
                  </circle>
                  <circle cx="-100" cy="50" r="2" fill="#2F80ED" opacity="0.9">
                    <animate attributeName="r" values="2;4;2" duration="2s" begin="1.5s" repeatCount="indefinite" />
                  </circle>
                  <circle cx="100" cy="50" r="2" fill="#2F80ED" opacity="0.9">
                    <animate attributeName="r" values="2;4;2" duration="2s" begin="0.3s" repeatCount="indefinite" />
                  </circle>
                </motion.g>
              </motion.svg>

              {/* Info Labels */}
              <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-full bg-slate-950/80 backdrop-blur-sm border border-[#2F80ED]/30 z-10">
                <span className="text-xs text-slate-300">Interactive 3D Model</span>
              </div>

              <div className="absolute top-4 right-4 px-3 py-1.5 rounded-full bg-slate-950/80 backdrop-blur-sm border border-green-500/30 z-10">
                <span className="text-xs text-green-400">● Processing Complete</span>
              </div>
            </div>

            {/* Bottom Info Bar */}
            <div className="flex items-center justify-between p-4 bg-slate-950 border-t border-slate-800">
              <div className="flex items-center gap-6 text-sm text-slate-400">
                <span>Vertices: 2,847</span>
                <span>Faces: 1,523</span>
                <span>Processing Time: 18s</span>
              </div>
              <Button 
                size="sm" 
                className="bg-[#2F80ED] hover:bg-[#2563c4] text-white"
                onClick={handleViewFullDemo}
              >
                View Full Demo
              </Button>
            </div>
          </div>

          {/* Fullscreen Demo Dialog */}
          <Dialog open={isFullscreen} onOpenChange={setIsFullscreen}>
            <DialogContent className="max-w-6xl bg-slate-900 border-slate-800 p-0 overflow-hidden">
              <DialogHeader className="p-6 pb-0">
                <DialogTitle className="text-white">Blueprint to 3D Conversion Demo</DialogTitle>
              </DialogHeader>
              <div className="relative aspect-video bg-gradient-to-br from-slate-950 to-black p-8">
                <div className="grid grid-cols-2 gap-8 h-full">
                  {/* Left: 2D Blueprint */}
                  <motion.div 
                    className="relative border-2 border-[#2F80ED]/30 rounded-lg p-6 bg-slate-900/50 overflow-hidden"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6 }}
                  >
                    <div className="absolute top-2 left-2 px-3 py-1 bg-slate-800 rounded text-xs text-slate-300">
                      2D Blueprint Input
                    </div>
                    <svg className="w-full h-full" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
                      {/* Floor Plan */}
                      <rect x="50" y="50" width="300" height="200" fill="none" stroke="#2F80ED" strokeWidth="3" opacity="0.7" />
                      <line x1="50" y1="150" x2="350" y2="150" stroke="#2F80ED" strokeWidth="2" opacity="0.5" />
                      <line x1="200" y1="50" x2="200" y2="250" stroke="#2F80ED" strokeWidth="2" opacity="0.5" />
                      <motion.path 
                        d="M 120 150 Q 135 135 150 150" 
                        fill="none" 
                        stroke="#2F80ED" 
                        strokeWidth="2"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 1, delay: 0.5, repeat: Infinity, repeatDelay: 2 }}
                      />
                      <rect x="100" y="48" width="40" height="4" fill="#2F80ED" opacity="0.6" />
                      <rect x="260" y="48" width="40" height="4" fill="#2F80ED" opacity="0.6" />
                      <rect x="70" y="170" width="50" height="60" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.4" strokeDasharray="5,5" />
                      <rect x="220" y="70" width="60" height="60" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.4" strokeDasharray="5,5" />
                      <text x="200" y="40" textAnchor="middle" fill="#2F80ED" fontSize="12" opacity="0.5">12.5m</text>
                      <text x="30" y="150" textAnchor="middle" fill="#2F80ED" fontSize="12" opacity="0.5">8m</text>
                      <motion.line 
                        x1="50" 
                        x2="350" 
                        stroke="#2F80ED" 
                        strokeWidth="1" 
                        opacity="0.8"
                        initial={{ y1: 50, y2: 50 }}
                        animate={{ y1: 250, y2: 250 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      />
                    </svg>
                  </motion.div>

                  {/* Right: 3D Model */}
                  <motion.div 
                    className="relative border-2 border-[#2F80ED]/50 rounded-lg p-6 bg-gradient-to-br from-slate-800/50 to-slate-900/50 overflow-hidden"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                  >
                    <div className="absolute top-2 left-2 px-3 py-1 bg-[#2F80ED]/20 rounded text-xs text-[#2F80ED]">
                      3D Model Output
                    </div>
                    <svg className="w-full h-full" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
                      <motion.g transform="translate(200, 150)">
                        <motion.path d="M -100 60 L 100 60 L 120 40 L -80 40 Z" fill="rgba(47, 128, 237, 0.05)" stroke="#2F80ED" strokeWidth="2" opacity="0.7" initial={{ opacity: 0 }} animate={{ opacity: 0.7 }} transition={{ duration: 0.5, delay: 1 }} />
                        <motion.path d="M -80 40 L 120 40 L 120 -60 L -80 -60 Z" fill="rgba(47, 128, 237, 0.03)" stroke="#2F80ED" strokeWidth="1.5" opacity="0.5" initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ duration: 0.5, delay: 1.2 }} />
                        <motion.path d="M -100 60 L -80 40 L -80 -60 L -100 -40 Z" fill="rgba(47, 128, 237, 0.08)" stroke="#2F80ED" strokeWidth="2" opacity="0.8" initial={{ opacity: 0 }} animate={{ opacity: 0.8 }} transition={{ duration: 0.5, delay: 1.4 }} />
                        <motion.path d="M -100 60 L 100 60 L 100 -40 L -100 -40 Z" fill="rgba(47, 128, 237, 0.1)" stroke="#2F80ED" strokeWidth="2.5" opacity="0.9" initial={{ opacity: 0 }} animate={{ opacity: 0.9 }} transition={{ duration: 0.5, delay: 1.6 }} />
                        <motion.path d="M -100 -40 L 0 -90 L 100 -40" fill="rgba(47, 128, 237, 0.07)" stroke="#2F80ED" strokeWidth="2" opacity="0.8" initial={{ opacity: 0 }} animate={{ opacity: 0.8 }} transition={{ duration: 0.5, delay: 1.8 }} />
                        <motion.rect x="-15" y="15" width="30" height="45" fill="rgba(47, 128, 237, 0.2)" stroke="#2F80ED" strokeWidth="2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3, delay: 2 }} />
                        <motion.rect x="-70" y="-10" width="30" height="30" fill="rgba(100, 200, 255, 0.3)" stroke="#2F80ED" strokeWidth="1.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3, delay: 2.2 }} />
                        <motion.rect x="40" y="-10" width="30" height="30" fill="rgba(100, 200, 255, 0.3)" stroke="#2F80ED" strokeWidth="1.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3, delay: 2.4 }} />
                        <circle cx="-100" cy="-40" r="3" fill="#2F80ED" opacity="0.9">
                          <animate attributeName="r" values="3;5;3" duration="2s" repeatCount="indefinite" />
                        </circle>
                        <circle cx="100" cy="-40" r="3" fill="#2F80ED" opacity="0.9">
                          <animate attributeName="r" values="3;5;3" duration="2s" begin="0.5s" repeatCount="indefinite" />
                        </circle>
                        <circle cx="0" cy="-90" r="3" fill="#2F80ED" opacity="0.9">
                          <animate attributeName="r" values="3;5;3" duration="2s" begin="1s" repeatCount="indefinite" />
                        </circle>
                      </motion.g>
                    </svg>
                    <motion.div className="absolute bottom-2 right-2 px-3 py-1 bg-green-500/20 border border-green-500/40 rounded text-xs text-green-400" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.5 }}>
                      ✓ Conversion Complete
                    </motion.div>
                  </motion.div>
                </div>
                
                <motion.div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, delay: 0.8 }}>
                  <div className="bg-slate-900 border-2 border-[#2F80ED] rounded-full p-3">
                    <ArrowRight className="w-8 h-8 text-[#2F80ED]" />
                  </div>
                </motion.div>
              </div>
              <div className="p-6 pt-4 bg-slate-900/50">
                <p className="text-slate-400 text-sm">
                  Experience the complete workflow: from blueprint upload to 3D visualization in real-time.
                </p>
              </div>
            </DialogContent>
          </Dialog>
        </motion.div>

        {/* Feature Highlights */}
        <motion.div 
          className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <div className="text-center p-6 rounded-lg bg-slate-900/50 border border-slate-800">
            <div className="text-3xl mb-2 text-[#2F80ED]">360°</div>
            <div className="text-sm text-slate-400">Full rotation & navigation</div>
          </div>
          <div className="text-center p-6 rounded-lg bg-slate-900/50 border border-slate-800">
            <div className="text-3xl mb-2 text-[#2F80ED]">Real-time</div>
            <div className="text-sm text-slate-400">Instant updates & edits</div>
          </div>
          <div className="text-center p-6 rounded-lg bg-slate-900/50 border border-slate-800">
            <div className="text-3xl mb-2 text-[#2F80ED]">AR Ready</div>
            <div className="text-sm text-slate-400">Export to AR/VR devices</div>
          </div>
        </motion.div>
      </div>
    </section>
    </>
  );
}
