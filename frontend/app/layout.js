import "./globals.css";
import { AppShell } from "../components/app-shell";
import { AuthGate } from "../components/auth-gate";
import { AuthProvider } from "../components/auth-provider";

export const metadata = {
  title: "Timetabling Assistant",
  description: "Admin frontend for tutoring-centre scheduling",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AuthGate>
            <AppShell>{children}</AppShell>
          </AuthGate>
        </AuthProvider>
      </body>
    </html>
  );
}
