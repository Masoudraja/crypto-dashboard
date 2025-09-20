import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar"; // Import the new Sidebar

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Crypto Analytics Dashboard",
  description: "A professional dashboard for crypto analysis and prediction.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex">
          <Sidebar />
          <main className="flex-1 ml-64 bg-slate-50 min-h-screen">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}