import { Building2, Users, Presentation, Home } from "lucide-react";
import { motion } from "motion/react";

const useCases = [
  {
    icon: Building2,
    title: "Architecture Firms",
    description: "Accelerate design reviews and client presentations with instant 3D visualizations"
  },
  {
    icon: Users,
    title: "Real Estate",
    description: "Give buyers immersive property tours before construction even begins"
  },
  {
    icon: Presentation,
    title: "Construction Teams",
    description: "Improve planning and coordination with accurate spatial models"
  },
  {
    icon: Home,
    title: "Interior Designers",
    description: "Visualize spaces in 3D and AR to make better design decisions"
  }
];

export function UseCases() {
  return (
    <section className="py-24 bg-slate-950 relative overflow-hidden">
      {/* Tech Pattern Background */}
      <div className="absolute top-0 left-0 w-full h-64 opacity-20">
        <div className="absolute inset-0 bg-gradient-to-b from-[#2F80ED]/20 to-transparent" />
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
            Built for Professionals
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Trusted by industry leaders across architecture, real estate, and construction
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {useCases.map((useCase, index) => (
            <motion.div
              key={index}
              className="relative p-8 rounded-lg bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 hover:border-[#2F80ED]/50 transition-all duration-300 group overflow-hidden"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              {/* Hover Gradient Effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#2F80ED]/0 to-blue-600/0 group-hover:from-[#2F80ED]/10 group-hover:to-blue-600/10 transition-all duration-300" />
              
              <div className="relative z-10">
                <div className="mb-4 inline-flex p-4 rounded-lg bg-slate-800 border border-slate-700 group-hover:border-[#2F80ED]/50 transition-colors">
                  <useCase.icon className="w-8 h-8 text-[#2F80ED]" />
                </div>
                
                <h3 className="text-xl mb-3 text-white">
                  {useCase.title}
                </h3>
                
                <p className="text-slate-400">
                  {useCase.description}
                </p>
              </div>

              {/* Corner Accent */}
              <div className="absolute top-0 right-0 w-16 h-16 border-t border-r border-[#2F80ED]/0 group-hover:border-[#2F80ED]/30 transition-colors" />
            </motion.div>
          ))}
        </div>

        {/* Stats Section */}
        <motion.div 
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="text-center">
            <div className="text-4xl md:text-5xl mb-2 bg-gradient-to-r from-[#2F80ED] to-blue-500 bg-clip-text text-transparent">10k+</div>
            <div className="text-slate-400">Projects Converted</div>
          </div>
          <div className="text-center">
            <div className="text-4xl md:text-5xl mb-2 bg-gradient-to-r from-[#2F80ED] to-blue-500 bg-clip-text text-transparent">98%</div>
            <div className="text-slate-400">Accuracy Rate</div>
          </div>
          <div className="text-center">
            <div className="text-4xl md:text-5xl mb-2 bg-gradient-to-r from-[#2F80ED] to-blue-500 bg-clip-text text-transparent"><30s</div>
            <div className="text-slate-400">Average Process Time</div>
          </div>
          <div className="text-center">
            <div className="text-4xl md:text-5xl mb-2 bg-gradient-to-r from-[#2F80ED] to-blue-500 bg-clip-text text-transparent">500+</div>
            <div className="text-slate-400">Enterprise Clients</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
