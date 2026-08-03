import ClientModuleShell from "../../components/navigation/ClientModuleShell";
import { AuditContextProvider } from "../../lib/hooks/useAuditContext";

export default function EntityProfileLayout({ children }: { children: React.ReactNode }) {
  return <AuditContextProvider><ClientModuleShell>{children}</ClientModuleShell></AuditContextProvider>;
}
