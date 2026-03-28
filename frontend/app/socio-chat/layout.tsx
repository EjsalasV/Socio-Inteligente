import ClientModuleShell from "../../components/navigation/ClientModuleShell";
import { AuditContextProvider } from "../../lib/hooks/useAuditContext";

export default function SocioChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuditContextProvider>
      <ClientModuleShell>{children}</ClientModuleShell>
    </AuditContextProvider>
  );
}
