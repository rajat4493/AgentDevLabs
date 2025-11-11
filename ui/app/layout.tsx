import "./globals.css";
export const metadata = {
  title: "AgenticLabs",
  description: "Agentic AI Observability & Governance"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head />
      <body className="min-h-dvh bg-gray-50">
        {children}
      </body>
    </html>
  );
}
