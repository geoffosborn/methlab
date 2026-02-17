import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "MethLab - Making Invisible Emissions Visible",
    template: "%s | MethLab",
  },
  description:
    "Real satellite methane plume data visualized as immersive 3D volumetric plumes. Exposing fugitive emissions from oil & gas, coal, and waste facilities worldwide.",
  keywords: [
    "methane",
    "emissions",
    "satellite",
    "visualization",
    "climate",
    "fugitive emissions",
    "carbon mapper",
    "greenhouse gas",
  ],
  openGraph: {
    title: "MethLab - Making Invisible Emissions Visible",
    description:
      "Real satellite methane data as immersive 3D volumetric plumes.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans antialiased bg-black text-white`}
      >
        <Header />
        <main className="min-h-screen pt-14">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
