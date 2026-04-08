"use client";

import { useEffect, useMemo, useState } from "react";

export type LearningRole = "junior" | "semi" | "senior" | "socio";

const STORAGE_KEY = "learning:v1:role";

function normalizeRole(value: string | null): LearningRole {
  if (value === "junior" || value === "semi" || value === "senior" || value === "socio") return value;
  return "semi";
}

export function useLearningRole(): {
  role: LearningRole;
  setRole: (role: LearningRole) => void;
  roleLabel: string;
} {
  const [role, setRoleState] = useState<LearningRole>("semi");

  useEffect(() => {
    if (typeof window === "undefined") return;
    setRoleState(normalizeRole(window.localStorage.getItem(STORAGE_KEY)));
  }, []);

  const setRole = (nextRole: LearningRole): void => {
    setRoleState(nextRole);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, nextRole);
    }
  };

  const roleLabel = useMemo(() => {
    if (role === "junior") return "Junior";
    if (role === "socio") return "Socio";
    if (role === "senior") return "Senior";
    return "Semi Senior";
  }, [role]);

  return { role, setRole, roleLabel };
}
