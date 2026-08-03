"use client";

import { usePathname } from "next/navigation";

import LegalFooter from "../legal/LegalFooter";

const HIDDEN_PATHS = new Set(["/", "/landing"]);

export default function ConditionalLegalFooter() {
  const pathname = usePathname();

  if (HIDDEN_PATHS.has(pathname)) {
    return null;
  }

  return <LegalFooter />;
}
