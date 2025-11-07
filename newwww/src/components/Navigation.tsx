import { Button } from "./ui/button";
import { Menu, X } from "lucide-react";
import { useState } from "react";

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-slate-800">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#2F80ED] to-blue-600 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-white rounded" />
            </div>
            <span className="text-2xl text-white">Skematix</span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#" className="text-slate-300 hover:text-[#2F80ED] transition-colors">
              Home
            </a>
            <a href="#features" className="text-slate-300 hover:text-[#2F80ED] transition-colors">
              Features
            </a>
            <a href="#demo" className="text-slate-300 hover:text-[#2F80ED] transition-colors">
              Demo
            </a>
            <a href="#about" className="text-slate-300 hover:text-[#2F80ED] transition-colors">
              About
            </a>
            <a href="#contact" className="text-slate-300 hover:text-[#2F80ED] transition-colors">
              Contact
            </a>
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Button className="bg-[#2F80ED] hover:bg-[#2563c4] text-white">
              Try Now
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-slate-300 hover:text-cyan-400"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="md:hidden py-4 border-t border-slate-800">
            <div className="flex flex-col gap-4">
              <a href="#" className="text-slate-300 hover:text-[#2F80ED] transition-colors py-2">
                Home
              </a>
              <a href="#features" className="text-slate-300 hover:text-[#2F80ED] transition-colors py-2">
                Features
              </a>
              <a href="#demo" className="text-slate-300 hover:text-[#2F80ED] transition-colors py-2">
                Demo
              </a>
              <a href="#about" className="text-slate-300 hover:text-[#2F80ED] transition-colors py-2">
                About
              </a>
              <a href="#contact" className="text-slate-300 hover:text-[#2F80ED] transition-colors py-2">
                Contact
              </a>
              <div className="flex flex-col gap-2 pt-4 border-t border-slate-800">
                <Button className="bg-[#2F80ED] hover:bg-[#2563c4] text-white w-full">
                  Try Now
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
