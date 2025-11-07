import { Button } from "./ui/button";
import { Upload, Play, ArrowRight, X } from "lucide-react";
import { motion } from "motion/react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { useState, useRef } from "react";

export function Hero() {
  const [isVideoOpen, setIsVideoOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleOpenVideo = () => {
    setIsVideoOpen(true);
  };

  const handleCloseVideo = () => {
    setIsVideoOpen(false);
    if (videoRef.current) {
      videoRef.current.pause();
    }
  };

  return (
    <>
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-black">
      {/* Blueprint Grid Background */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(47, 128, 237, 0.3) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(47, 128, 237, 0.3) 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }} />
      </div>

      {/* Glowing Dots Effect */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-[#2F80ED] rounded-full blur-sm animate-pulse" />
        <div className="absolute top-1/3 right-1/3 w-2 h-2 bg-[#2F80ED] rounded-full blur-sm animate-pulse delay-100" />
        <div className="absolute bottom-1/3 left-1/2 w-2 h-2 bg-[#2F80ED] rounded-full blur-sm animate-pulse delay-200" />
      </div>

      {/* 3D Wireframe Accents */}
      <motion.div 
        className="absolute top-20 right-20 w-64 h-64 border border-[#2F80ED]/20"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, delay: 0.5 }}
      >
        <div className="absolute inset-4 border border-[#2F80ED]/15" />
        <div className="absolute inset-8 border border-[#2F80ED]/10" />
      </motion.div>

      <motion.div 
        className="absolute bottom-32 left-20 w-48 h-48 border border-[#2F80ED]/20 rotate-45"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, delay: 0.7 }}
      >
        <div className="absolute inset-4 border border-[#2F80ED]/15" />
      </motion.div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Side - Text Content */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl mb-6 text-white leading-tight">
              See Beyond<br />the Lines
            </h1>
            
            <p className="text-xl md:text-2xl mb-12 text-slate-300">
              Convert 2D blueprints into immersive 3D models with AI.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className="bg-[#2F80ED] hover:bg-[#2563c4] text-white px-8 group">
                <Upload className="mr-2 w-5 h-5" />
                Upload Blueprint
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-slate-600 text-slate-300 hover:bg-slate-800"
                onClick={handleOpenVideo}
              >
                <Play className="mr-2 w-5 h-5" />
                Watch Demo
              </Button>
            </div>

            {/* Demo Dialog */}
            <Dialog open={isVideoOpen} onOpenChange={setIsVideoOpen}>
              <DialogContent className="max-w-5xl bg-slate-900 border-slate-800 p-0 overflow-hidden">
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
                        
                        {/* Rooms */}
                        <line x1="50" y1="150" x2="350" y2="150" stroke="#2F80ED" strokeWidth="2" opacity="0.5" />
                        <line x1="200" y1="50" x2="200" y2="250" stroke="#2F80ED" strokeWidth="2" opacity="0.5" />
                        
                        {/* Doors */}
                        <motion.path 
                          d="M 120 150 Q 135 135 150 150" 
                          fill="none" 
                          stroke="#2F80ED" 
                          strokeWidth="2"
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ duration: 1, delay: 0.5, repeat: Infinity, repeatDelay: 2 }}
                        />
                        
                        {/* Windows */}
                        <rect x="100" y="48" width="40" height="4" fill="#2F80ED" opacity="0.6" />
                        <rect x="260" y="48" width="40" height="4" fill="#2F80ED" opacity="0.6" />
                        
                        {/* Furniture outlines */}
                        <rect x="70" y="170" width="50" height="60" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.4" strokeDasharray="5,5" />
                        <rect x="220" y="70" width="60" height="60" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.4" strokeDasharray="5,5" />
                        
                        {/* Dimensions */}
                        <text x="200" y="40" textAnchor="middle" fill="#2F80ED" fontSize="12" opacity="0.5">12.5m</text>
                        <text x="30" y="150" textAnchor="middle" fill="#2F80ED" fontSize="12" opacity="0.5">8m</text>
                        
                        {/* Scanning effect */}
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
                        <motion.g 
                          transform="translate(200, 150)"
                          initial={{ rotateY: 0 }}
                          animate={{ rotateY: 360 }}
                          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                        >
                          {/* 3D House Structure */}
                          {/* Floor */}
                          <motion.path 
                            d="M -100 60 L 100 60 L 120 40 L -80 40 Z" 
                            fill="rgba(47, 128, 237, 0.05)" 
                            stroke="#2F80ED" 
                            strokeWidth="2" 
                            opacity="0.7"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 0.7 }}
                            transition={{ duration: 0.5, delay: 1 }}
                          />
                          
                          {/* Back Wall */}
                          <motion.path 
                            d="M -80 40 L 120 40 L 120 -60 L -80 -60 Z" 
                            fill="rgba(47, 128, 237, 0.03)" 
                            stroke="#2F80ED" 
                            strokeWidth="1.5" 
                            opacity="0.5"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 0.5 }}
                            transition={{ duration: 0.5, delay: 1.2 }}
                          />
                          
                          {/* Left Wall */}
                          <motion.path 
                            d="M -100 60 L -80 40 L -80 -60 L -100 -40 Z" 
                            fill="rgba(47, 128, 237, 0.08)" 
                            stroke="#2F80ED" 
                            strokeWidth="2" 
                            opacity="0.8"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 0.8 }}
                            transition={{ duration: 0.5, delay: 1.4 }}
                          />
                          
                          {/* Front Wall */}
                          <motion.path 
                            d="M -100 60 L 100 60 L 100 -40 L -100 -40 Z" 
                            fill="rgba(47, 128, 237, 0.1)" 
                            stroke="#2F80ED" 
                            strokeWidth="2.5" 
                            opacity="0.9"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 0.9 }}
                            transition={{ duration: 0.5, delay: 1.6 }}
                          />
                          
                          {/* Roof */}
                          <motion.path 
                            d="M -100 -40 L 0 -90 L 100 -40" 
                            fill="rgba(47, 128, 237, 0.07)" 
                            stroke="#2F80ED" 
                            strokeWidth="2" 
                            opacity="0.8"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 0.8 }}
                            transition={{ duration: 0.5, delay: 1.8 }}
                          />
                          
                          {/* Door */}
                          <motion.rect 
                            x="-15" 
                            y="15" 
                            width="30" 
                            height="45" 
                            fill="rgba(47, 128, 237, 0.2)" 
                            stroke="#2F80ED" 
                            strokeWidth="2"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3, delay: 2 }}
                          />
                          
                          {/* Windows */}
                          <motion.rect 
                            x="-70" 
                            y="-10" 
                            width="30" 
                            height="30" 
                            fill="rgba(100, 200, 255, 0.3)" 
                            stroke="#2F80ED" 
                            strokeWidth="1.5"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3, delay: 2.2 }}
                          />
                          <motion.rect 
                            x="40" 
                            y="-10" 
                            width="30" 
                            height="30" 
                            fill="rgba(100, 200, 255, 0.3)" 
                            stroke="#2F80ED" 
                            strokeWidth="1.5"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3, delay: 2.4 }}
                          />
                          
                          {/* Vertex Points */}
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
                      
                      {/* Processing badge */}
                      <motion.div 
                        className="absolute bottom-2 right-2 px-3 py-1 bg-green-500/20 border border-green-500/40 rounded text-xs text-green-400"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 2.5 }}
                      >
                        ✓ Conversion Complete
                      </motion.div>
                    </motion.div>
                  </div>
                  
                  {/* Processing Arrow */}
                  <motion.div 
                    className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.8 }}
                  >
                    <div className="bg-slate-900 border-2 border-[#2F80ED] rounded-full p-3">
                      <ArrowRight className="w-8 h-8 text-[#2F80ED]" />
                    </div>
                  </motion.div>
                </div>
                <div className="p-6 pt-4 bg-slate-900/50">
                  <p className="text-slate-400 text-sm">
                    Watch how Skematix transforms 2D blueprints into immersive 3D models using AI-powered computer vision in real-time.
                  </p>
                </div>
              </DialogContent>
            </Dialog>
          </motion.div>

          {/* Right Side - Transformation Visual */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="relative p-8 rounded-lg border border-slate-800 bg-slate-900/50 backdrop-blur-sm">
              {/* Blueprint Icon */}
              <div className="absolute -top-6 left-8 bg-slate-900 px-4 py-2 rounded-full border border-[#2F80ED]/30">
                <span className="text-sm text-slate-300">2D Blueprint</span>
              </div>
              
              <div className="mb-6 p-6 bg-slate-800/50 rounded border border-slate-700">
                <svg className="w-full h-48" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
                  <rect x="50" y="50" width="300" height="100" fill="none" stroke="#2F80ED" strokeWidth="2" opacity="0.6" />
                  <line x1="50" y1="100" x2="350" y2="100" stroke="#2F80ED" strokeWidth="1" opacity="0.4" strokeDasharray="5,5" />
                  <rect x="80" y="70" width="40" height="60" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.5" />
                  <rect x="280" y="70" width="40" height="60" fill="none" stroke="#2F80ED" strokeWidth="1.5" opacity="0.5" />
                </svg>
              </div>

              {/* Arrow */}
              <div className="flex justify-center mb-6">
                <ArrowRight className="w-8 h-8 text-[#2F80ED] animate-pulse" />
              </div>

              {/* 3D Model Icon */}
              <div className="absolute -bottom-6 right-8 bg-slate-900 px-4 py-2 rounded-full border border-[#2F80ED]/30">
                <span className="text-sm text-slate-300">3D Model</span>
              </div>

              <div className="p-6 bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded border border-[#2F80ED]/30">
                <svg className="w-full h-48" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
                  {/* 3D Wireframe Cube */}
                  <g transform="translate(200, 100)">
                    {/* Back face */}
                    <path d="M -60 -30 L 60 -30 L 60 30 L -60 30 Z" fill="none" stroke="#2F80ED" strokeWidth="1" opacity="0.3" />
                    {/* Front face */}
                    <path d="M -80 -10 L 40 -10 L 40 50 L -80 50 Z" fill="none" stroke="#2F80ED" strokeWidth="2" opacity="0.8" />
                    {/* Connecting lines */}
                    <line x1="-60" y1="-30" x2="-80" y2="-10" stroke="#2F80ED" strokeWidth="1" opacity="0.5" />
                    <line x1="60" y1="-30" x2="40" y2="-10" stroke="#2F80ED" strokeWidth="1" opacity="0.5" />
                    <line x1="60" y1="30" x2="40" y2="50" stroke="#2F80ED" strokeWidth="1" opacity="0.5" />
                    <line x1="-60" y1="30" x2="-80" y2="50" stroke="#2F80ED" strokeWidth="1" opacity="0.5" />
                  </g>
                </svg>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
    </>
  );
}
