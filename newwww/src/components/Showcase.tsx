import { motion } from "motion/react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { ArrowRight } from "lucide-react";
import { Button } from "./ui/button";

export function Showcase() {
  return (
    <section className="py-24 bg-slate-900 relative overflow-hidden">
      {/* Wireframe Grid Background */}
      <div className="absolute inset-0 opacity-10">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="wireframe" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
              <path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgb(148, 163, 184)" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#wireframe)" />
        </svg>
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="relative">
              {/* Decorative Corner Frame */}
              <div className="absolute -top-4 -left-4 w-24 h-24 border-t-4 border-l-4 border-[#2F80ED]/30" />
              <div className="absolute -bottom-4 -right-4 w-24 h-24 border-b-4 border-r-4 border-[#2F80ED]/30" />
              
              <div className="relative rounded-lg overflow-hidden border border-slate-700">
                <ImageWithFallback
                  src="https://images.unsplash.com/photo-1713643957213-4a6acc242563?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmdXR1cmlzdGljJTIwYXJjaGl0ZWN0dXJlJTIwM0R8ZW58MXx8fHwxNzYyNDUzNTEzfDA&ixlib=rb-4.1.0&q=80&w=1080"
                  alt="3D architectural visualization"
                  className="w-full h-[500px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
              </div>
            </div>
          </motion.div>

          <motion.div
            className="space-y-6"
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-block px-4 py-2 rounded-full border border-[#2F80ED]/30 bg-[#2F80ED]/10">
              <span className="text-[#2F80ED] text-sm">Next-Gen Visualization</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl text-white">
              Experience Architecture in a New Dimension
            </h2>
            
            <p className="text-lg text-slate-400">
              Skematix doesn't just convert blueprints—it brings them to life. Our AI understands spatial relationships, 
              materials, and architectural conventions to create models that are both accurate and beautiful.
            </p>

            <div className="space-y-4">
              <div className="flex items-start gap-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <div className="w-2 h-2 rounded-full bg-[#2F80ED] mt-2" />
                <div>
                  <h4 className="text-white mb-1">Photorealistic Rendering</h4>
                  <p className="text-slate-400 text-sm">Apply materials, lighting, and textures for stunning visualizations</p>
                </div>
              </div>
              
              <div className="flex items-start gap-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <div className="w-2 h-2 rounded-full bg-[#2F80ED] mt-2" />
                <div>
                  <h4 className="text-white mb-1">Real-Time Collaboration</h4>
                  <p className="text-slate-400 text-sm">Share and edit models with your team in real-time</p>
                </div>
              </div>
              
              <div className="flex items-start gap-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <div className="w-2 h-2 rounded-full bg-[#2F80ED] mt-2" />
                <div>
                  <h4 className="text-white mb-1">Multi-Format Export</h4>
                  <p className="text-slate-400 text-sm">Export to OBJ, FBX, GLTF, and more for any workflow</p>
                </div>
              </div>
            </div>

            <Button size="lg" className="bg-[#2F80ED] hover:bg-[#2563c4] text-white px-8 group">
              Learn More
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
