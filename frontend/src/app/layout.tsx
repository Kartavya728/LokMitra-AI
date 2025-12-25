import type { Metadata } from "next";
import "./globals.css";
import { CallingListProvider } from "@/contexts/CallingListContext";

export const metadata: Metadata = {
  title: "LokMitra AI - Responsive AI Dashboard",
  description: "AI-powered dashboard for government and corporate entities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <CallingListProvider>
          {children}
        </CallingListProvider>
      </body>
    </html>
  );
}
