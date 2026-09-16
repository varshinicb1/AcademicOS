import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppShell } from "@/components/shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "AcademicOS",
  description: "Evidence-grounded academic operating system for CBSE/NCERT schools",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
