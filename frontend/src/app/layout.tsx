import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const themeScript = `
  (function () {
    try {
      const savedTheme = localStorage.getItem('ai_competitor_research_theme');
      const theme = savedTheme === 'dark' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme);
    } catch (error) {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  })();
`;

export const metadata: Metadata = {
  title: "Research Room | AI Competitor Research",
  description: "A focused workspace for competitor research and market intelligence.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
