import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import "./globals.css";
import "./corporate-shell.css";

export const metadata: Metadata = {
  title: "Ora Tributa",
  description: "Fundação auditável para inteligência tributária brasileira.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body><AppShell>{children}</AppShell></body>
    </html>
  );
}
