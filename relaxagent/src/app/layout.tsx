import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RelaxAgent",
  description: "A simple LobeHub-inspired chat workspace.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
