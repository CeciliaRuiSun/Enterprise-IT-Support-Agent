import type { Metadata } from "next";

import "./globals.css";
import { EntraAuthProvider } from "@/components/auth-provider";

export const metadata: Metadata = {
  title: "Enterprise IT Support Agent",
  description: "An enterprise-oriented IT support chat MVP with knowledge retrieval and ticket workflows."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <EntraAuthProvider>{children}</EntraAuthProvider>
      </body>
    </html>
  );
}
