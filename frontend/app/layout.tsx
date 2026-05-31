import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SupplyPulse V2",
  description: "Evidence-backed delivery exposure control tower",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}