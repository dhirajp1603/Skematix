import { Brain, Box, Palette, Glasses } from "lucide-react";
import { motion } from "motion/react";

const features = [
  {
    icon: Brain,
    title: "AI Room Detection",
    description: "Advanced computer vision algorithms automatically identify rooms, walls, doors, and windows from your 2D blueprints with precision.",
    emoji: "🧠"
  },
  {
    icon: Box,
    title: "Automatic 3D Generation",
    description: "Instantly convert floor plans into accurate, fully navigable 3D models. No manual modeling required.",
    emoji: "🏗️"
  },
  {
    icon: Palette,
    title: "Interior Suggestions",
    description: "Get AI-powered design recommendations for furniture placement, color schemes, and spatial optimization.",
    emoji: "🎨"
  },
  {
    icon: Glasses,
    title: "AR/VR Visualization",
    description: "Experience your designs in augmented and virtual reality. Walk through spaces before they're built.",
    emoji: "🌐"
  }
];

export function Features() {
  return (
    <section className="py-24 bg-slate-950 relative overflow-hidden">
      {/* Grid Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(148, 163, 184, 0.5) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(148, 163, 184, 0.5) 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }} />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl mb-4 text-white">
            Powerful Features
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Everything you need to transform architectural drawings into interactive 3D experiences
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="relative p-8 rounded-lg border border-slate-800 bg-slate-900/50 backdrop-blur-sm hover:border-[#2F80ED]/50 transition-all duration-300 group"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Corner Accent */}
              <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-[#2F80ED]/20 group-hover:border-[#2F80ED]/50 transition-colors" />
              <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-[#2F80ED]/20 group-hover:border-[#2F80ED]/50 transition-colors" />
              
              <div className="mb-4 flex items-center gap-3">
                <span className="text-3xl">{feature.emoji}</span>
                <div className="inline-flex p-2 rounded-lg bg-[#2F80ED]/10 border border-[#2F80ED]/20">
                  <feature.icon className="w-6 h-6 text-[#2F80ED]" />
                </div>
              </div>
              
              <h3 className="text-xl mb-3 text-white">
                {feature.title}
              </h3>
              
              <p className="text-slate-400">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
