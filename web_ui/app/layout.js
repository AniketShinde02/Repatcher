import { Inter, Manrope, IBM_Plex_Mono } from 'next/font/google';
import './globals.css';
import LenisScroll from '@/components/lenis-scroll';

const inter = Inter({
    subsets: ['latin'],
    variable: '--font-sans',
    weight: ['400', '500', '600', '700'],
});

const manrope = Manrope({
    subsets: ['latin'],
    variable: '--font-display',
    weight: ['500', '600', '700', '800'],
});

const ibmPlexMono = IBM_Plex_Mono({
    subsets: ['latin'],
    variable: '--font-mono',
    weight: ['400', '500', '600', '700'],
});

export default function RootLayout({ children }) {
    return (
        <html lang='en' className={`${inter.variable} ${manrope.variable} ${ibmPlexMono.variable}`}>
            <LenisScroll />
            <body>{children}</body>
        </html>
    );
}
