import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ModernBank – Next-Gen Digital Banking",
  description: "AI-driven, real-time, cloud-native banking experience",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased bg-surface-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
