import "./globals.css";
import type { Metadata } from "next";
import PageTransition from "../components/navigation/PageTransition";
import SovereignCommandLazy from "../components/navigation/SovereignCommandLazy";
import AppStateProvider from "../components/providers/AppStateProvider";
import UserPreferencesProvider from "../components/providers/UserPreferencesProvider";
import TourProvider from "../components/tour/TourProvider";

export const metadata: Metadata = {
  title: "Socio AI — Plataforma de Auditoría Inteligente",
  description:
    "Automatiza la planificación, ejecución y documentación de auditorías. Motor de riesgos, papeles de trabajo y IA normativa para firmas independientes en LATAM.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" data-scroll-behavior="smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Newsreader:ital,wght@0,400;0,600;0,700;1,400&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <AppStateProvider>
          <UserPreferencesProvider>
            <TourProvider>
              <PageTransition>{children}</PageTransition>
              <SovereignCommandLazy />
            </TourProvider>
          </UserPreferencesProvider>
        </AppStateProvider>
      </body>
    </html>
  );
}
