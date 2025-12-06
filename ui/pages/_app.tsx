import type { AppProps } from "next/app";
import "@/styles/globals.css";

export default function RajosApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
