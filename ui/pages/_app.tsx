import type { AppProps } from "next/app";
import "@/styles/globals.css";
import { ThemeProvider } from "@/components/theme-provider";

export default function RajosApp({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <Component {...pageProps} />
    </ThemeProvider>
  );
}
