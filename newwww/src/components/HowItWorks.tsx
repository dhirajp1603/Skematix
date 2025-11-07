import { Upload, Cpu, Boxes, Download } from "lucide-react";
import { motion } from "motion/react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

const steps = [
  {
    icon: Upload,
    title: "Upload Blueprint",
    description: "Upload your 2D architectural drawings in PDF, PNG, or JPG format",
    step: "01"
  },
  {
    icon: Cpu,
    title: "AI Processing",
    description: "Our AI analyzes and identifies all architectural elements and spatial relationships",
    step: "02"
  },
  {
    icon: Boxes,
    title: "3D Generation",
    description: "Watch as your blueprint transforms into an accurate, navigable 3D model",
    step: "03"
  },
  {
    icon: Download,
    title: "Export & Share",
    description: "Export to popular 3D formats or share AR experiences with clients",
    step: "04"
  }
];

export function HowItWorks() {
  return (
    <section className="py-24 bg-gradient-to-b from-slate-950 to-slate-900 relative overflow-hidden">
      {/* Diagonal Lines Accent */}
      <div className="absolute top-0 right-0 w-1/3 h-full opacity-5">
        <div className="w-full h-full" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(47, 128, 237, 0.5) 35px, rgba(47, 128, 237, 0.5) 36px)'
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
            How It Works
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            From blueprint to 3D model in four simple steps
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              className="relative text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.15 }}
            >
              {/* Connection Line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-16 left-1/2 w-full h-0.5 bg-gradient-to-r from-[#2F80ED]/50 to-transparent" />
              )}
              
              <div className="relative inline-flex items-center justify-center mb-6">
                <div className="absolute w-24 h-24 rounded-full border-2 border-[#2F80ED]/20" />
                <div className="relative z-10 w-16 h-16 rounded-full bg-gradient-to-br from-[#2F80ED] to-blue-600 flex items-center justify-center">
                  <step.icon className="w-8 h-8 text-white" />
                </div>
                <div className="absolute -top-2 -right-2 w-10 h-10 rounded-full bg-slate-900 border border-[#2F80ED] flex items-center justify-center">
                  <span className="text-[#2F80ED] text-sm">{step.step}</span>
                </div>
              </div>
              
              <h3 className="text-xl mb-3 text-white">
                {step.title}
              </h3>
              
              <p className="text-slate-400">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Visual Example */}
        <motion.div
          className="mt-16 rounded-lg border border-slate-800 overflow-hidden"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <ImageWithFallback
            src="https://images.unsplash.com/photo-1762146828422-50a8bd416d3c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhcmNoaXRlY3R1cmFsJTIwYmx1ZXByaW50JTIwdGVjaG5pY2FsfGVufDF8fHx8MTc2MjQ1MzUxMnww&ixlib=rb-4.1.0&q=80&w=1080"
            alt="Blueprint to 3D conversion example"
            className="w-full h-[400px] object-cover"
          />
        </motion.div>
      </div>
    </section>
  );
}
