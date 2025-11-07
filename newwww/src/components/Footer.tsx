import { Twitter, Linkedin, Github, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-slate-950 border-t border-slate-800 py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#2F80ED] to-blue-600 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-white rounded" />
              </div>
              <span className="text-2xl text-white">Skematix</span>
            </div>
            <p className="text-slate-400 text-sm mb-4">
              See Beyond the Lines
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors">
                <Linkedin className="w-5 h-5" />
              </a>
              <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="#about" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  About
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Privacy
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  GitHub
                </a>
              </li>
              <li>
                <a href="#contact" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-white mb-4">Resources</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  API Reference
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Support
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Blog
                </a>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h4 className="text-white mb-4">Connect</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Twitter
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  LinkedIn
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  GitHub
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
                  Email Us
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-slate-400 text-sm">
            © 2025 Skematix. All rights reserved.
          </p>
          <div className="flex gap-6">
            <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
              Status
            </a>
            <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
              Security
            </a>
            <a href="#" className="text-slate-400 hover:text-[#2F80ED] transition-colors text-sm">
              Sitemap
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
