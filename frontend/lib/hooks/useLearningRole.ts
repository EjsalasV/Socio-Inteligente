"use client";

import { useMemo } from "react";

import { useUserPreferences } from "../../components/providers/UserPreferencesProvider";

export type LearningRole = "junior" | "semi" | "senior" | "socio";

export function useLearningRole(): {
  role: LearningRole;
  setRole: (role: LearningRole) => void;
  roleLabel: string;
} {
  const { preferences, patchPreferences } = useUserPreferences();
  const role = preferences.learning_role as LearningRole;
  const setRole = (nextRole: LearningRole): void => {
    void patchPreferences({ learning_role: nextRole });
  };

  const roleLabel = useMemo(() => {
    if (role === "junior") return "Junior";
    if (role === "socio") return "Socio";
    if (role === "senior") return "Senior";
    return "Semi Senior";
  }, [role]);

  return { role, setRole, roleLabel };
}
