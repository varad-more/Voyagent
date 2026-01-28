import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "Agentic Trip Planner",
  description: "LLM-driven itinerary planner with Gemini",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}
