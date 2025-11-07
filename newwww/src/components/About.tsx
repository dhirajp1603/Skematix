import { motion } from "motion/react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Target, Zap, Users } from "lucide-react";

export function About() {
  return (
    <section className="py-24 bg-slate-950 relative overflow-hidden">
      {/* Diagonal Lines Background */}
      <div className="absolute top-0 left-0 w-full h-full opacity-5">
        <div className="w-full h-full" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(47, 128, 237, 0.5) 35px, rgba(47, 128, 237, 0.5) 36px)'
        }} />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Side - Image */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="relative rounded-lg overflow-hidden border border-slate-800">
              {/* Corner Frames */}
              <div className="absolute top-0 left-0 w-20 h-20 border-t-4 border-l-4 border-[#2F80ED]/50 z-10" />
              <div className="absolute bottom-0 right-0 w-20 h-20 border-b-4 border-r-4 border-[#2F80ED]/50 z-10" />
              
              <ImageWithFallback
                src="https://images.unsplash.com/photo-1515733392795-4fbb2be3d1dd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWFtJTIwd29ya2luZyUyMGFyY2hpdGVjdHVyZSUyMG9mZmljZXxlbnwxfHx8fDE3NjI0NTM5Mjh8MA&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Team working on architectural designs"
                className="w-full h-[500px] object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent" />
            </div>

            {/* Floating Stats */}
            <motion.div 
              className="absolute -bottom-6 -left-6 bg-slate-900 border border-[#2F80ED]/30 rounded-lg p-4 backdrop-blur-sm"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <div className="text-3xl mb-1 text-[#2F80ED]">500+</div>
              <div className="text-sm text-slate-400">Projects Delivered</div>
            </motion.div>
          </motion.div>

          {/* Right Side - Content */}
          <motion.div
            className="space-y-6"
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-block px-4 py-2 rounded-full border border-[#2F80ED]/30 bg-[#2F80ED]/10">
              <span className="text-[#2F80ED] text-sm">About Skematix</span>
            </div>

            <h2 className="text-4xl md:text-5xl text-white">
              Our Mission
            </h2>

            <p className="text-lg text-slate-300 leading-relaxed">
              At Skematix, we believe that architectural visualization should be accessible, 
              instant, and intuitive. We're transforming the way architects, designers, and 
              construction professionals work by bridging the gap between 2D blueprints and 
              immersive 3D experiences.
            </p>

            <p className="text-lg text-slate-300 leading-relaxed">
              Our AI-powered platform combines cutting-edge computer vision with deep learning 
              to understand architectural drawings the way humans do—then brings them to life 
              in ways humans never could.
            </p>

            {/* Mission Points */}
            <div className="space-y-4 pt-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-[#2F80ED]/10 border border-[#2F80ED]/20">
                  <Target className="w-6 h-6 text-[#2F80ED]" />
                </div>
                <div>
                  <h4 className="text-white mb-1">Innovation First</h4>
                  <p className="text-slate-400 text-sm">
                    Pushing the boundaries of what's possible with AI and computer vision
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-[#2F80ED]/10 border border-[#2F80ED]/20">
                  <Zap className="w-6 h-6 text-[#2F80ED]" />
                </div>
                <div>
                  <h4 className="text-white mb-1">Speed & Accuracy</h4>
                  <p className="text-slate-400 text-sm">
                    Delivering precise 3D models in seconds, not hours
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-[#2F80ED]/10 border border-[#2F80ED]/20">
                  <Users className="w-6 h-6 text-[#2F80ED]" />
                </div>
                <div>
                  <h4 className="text-white mb-1">User-Centric Design</h4>
                  <p className="text-slate-400 text-sm">
                    Building tools that professionals actually want to use
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
