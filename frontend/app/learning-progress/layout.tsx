import ClientModuleShell from "../../components/navigation/ClientModuleShell";
import { AuditContextProvider } from "../../lib/hooks/useAuditContext";

export default function LearningProgressLayout({ children }: { children: React.ReactNode }) {
  return <AuditContextProvider><ClientModuleShell>{children}</ClientModuleShell></AuditContextProvider>;
}
