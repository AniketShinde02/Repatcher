'use client';
import { GithubIcon } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function Footer() {
    const links = [
        { name: 'Terms of Use', href: '/TERMS_OF_USE.md' },
        { name: 'Privacy Policy', href: '/PRIVACY.md' },
        { name: 'Security', href: '/SECURITY.md' },
        { name: 'Contributing', href: '/CONTRIBUTING.md' },
    ];
    return (
        <motion.footer className="flex flex-col items-center px-6 md:px-16 lg:px-24 justify-center w-full pt-12 mt-20 border-t border-white/10 bg-slate-950/80 backdrop-blur-xl text-slate-400 text-xs"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
        >
            <div className="flex flex-wrap items-center justify-center gap-8 py-4">
                {links.map((link, index) => (
                    <Link key={index} href={link.href} className="transition hover:text-white">
                        {link.name}
                    </Link>
                ))}
            </div>

            <hr className="w-full border-white/10 mt-4" />
            <div className="flex flex-col md:flex-row items-center w-full justify-between gap-4 py-6 text-slate-400">
                <p>AI Watermark Remover & Background Preserver v1.0.0 • Local Engine</p>
                <p>Copyright © 2026 Antigravity for Aniket. Apache 2.0 License.</p>
            </div>
        </motion.footer>
    );
};