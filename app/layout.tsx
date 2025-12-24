// frontend/app/layout.tsx

import type { Metadata } from "next";
import "./globals.css";

import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

export const metadata: Metadata = {
  title: "ConvoNest",
  description: "WhatsApp-first CRM platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <div className="flex min-h-screen">
          <Sidebar />

          <div className="flex flex-1 flex-col">
            <Topbar />

            <main className="flex-1 p-6">
              <div className="mx-auto max-w-6xl">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
