"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  defaultUserPreferences,
  getAuthMe,
  getUserPreferences,
  patchUserPreferences,
  type SessionUser,
  type UserPreferences,
  type UserPreferencesPatch,
} from "../../lib/api/user";

type UserPreferencesContextValue = {
  session: SessionUser | null;
  preferences: UserPreferences;
  loading: boolean;
  refresh: () => Promise<void>;
  patchPreferences: (patch: UserPreferencesPatch) => Promise<void>;
};

const UserPreferencesContext = createContext<UserPreferencesContextValue | null>(null);
const MIGRATION_MARK_PREFIX = "prefs:v1.2.1:migrated";

function hasSessionToken(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(window.localStorage.getItem("socio_token"));
}

function uniqueStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const value of values) {
    const item = String(value || "").trim();
    if (!item || seen.has(item)) continue;
    seen.add(item);
    out.push(item);
  }
  return out;
}

function mergePreferences(current: UserPreferences, patch: UserPreferencesPatch): UserPreferences {
  const next: UserPreferences = {
    learning_role: current.learning_role,
    tour_completed_modules: uniqueStrings(current.tour_completed_modules),
    tour_welcome_seen: current.tour_welcome_seen,
    onboarding_ui: {
      welcome_seen: current.onboarding_ui.welcome_seen,
      dismissed: current.onboarding_ui.dismissed,
      visited_modules_ui: uniqueStrings(current.onboarding_ui.visited_modules_ui),
    },
    preferences_version: current.preferences_version || "v1.2.1",
  };

  if (patch.learning_role) {
    next.learning_role = patch.learning_role;
  }
  if (patch.tour_completed_modules) {
    next.tour_completed_modules = uniqueStrings(patch.tour_completed_modules);
  }
  if (typeof patch.tour_welcome_seen === "boolean") {
    next.tour_welcome_seen = patch.tour_welcome_seen;
  }
  if (patch.onboarding_ui) {
    if (typeof patch.onboarding_ui.welcome_seen === "boolean") {
      next.onboarding_ui.welcome_seen = patch.onboarding_ui.welcome_seen;
    }
    if (typeof patch.onboarding_ui.dismissed === "boolean") {
      next.onboarding_ui.dismissed = patch.onboarding_ui.dismissed;
    }
    if (patch.onboarding_ui.visited_modules_ui) {
      next.onboarding_ui.visited_modules_ui = uniqueStrings(patch.onboarding_ui.visited_modules_ui);
    }
  }
  if (patch.preferences_version) {
    next.preferences_version = patch.preferences_version;
  }
  return next;
}

function readLegacyPatch(): UserPreferencesPatch {
  if (typeof window === "undefined") return {};
  const patch: UserPreferencesPatch = {};

  const learning = window.localStorage.getItem("learning:v1:role");
  if (learning === "junior" || learning === "semi" || learning === "senior" || learning === "socio") {
    patch.learning_role = learning;
  }

  try {
    const completed = JSON.parse(window.localStorage.getItem("tour:v1:completed_modules") || "[]");
    if (Array.isArray(completed) && completed.length) {
      patch.tour_completed_modules = completed.map((x) => String(x));
    }
  } catch {
    // ignore malformed local legacy.
  }

  const tourWelcome = window.localStorage.getItem("tour:v1:welcome_seen");
  if (tourWelcome === "true" || tourWelcome === "false") {
    patch.tour_welcome_seen = tourWelcome === "true";
  }

  const onboardingPatch: UserPreferencesPatch["onboarding_ui"] = {};
  const onboardingWelcome = window.localStorage.getItem("onboarding:v1:welcome_seen");
  if (onboardingWelcome === "true" || onboardingWelcome === "false") {
    onboardingPatch.welcome_seen = onboardingWelcome === "true";
  }
  const onboardingDismissed = window.localStorage.getItem("onboarding:v1:dismissed");
  if (onboardingDismissed === "true" || onboardingDismissed === "false") {
    onboardingPatch.dismissed = onboardingDismissed === "true";
  }
  try {
    const visited = JSON.parse(window.localStorage.getItem("onboarding:v1:visited_modules") || "[]");
    if (Array.isArray(visited) && visited.length) {
      onboardingPatch.visited_modules_ui = visited.map((x) => String(x));
    }
  } catch {
    // ignore malformed local legacy.
  }
  if (
    typeof onboardingPatch.welcome_seen === "boolean" ||
    typeof onboardingPatch.dismissed === "boolean" ||
    (onboardingPatch.visited_modules_ui && onboardingPatch.visited_modules_ui.length)
  ) {
    patch.onboarding_ui = onboardingPatch;
  }
  return patch;
}

export default function UserPreferencesProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<SessionUser | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>(defaultUserPreferences());
  const [loading, setLoading] = useState<boolean>(true);

  const patchPreferencesLocal = useCallback((patch: UserPreferencesPatch) => {
    setPreferences((prev) => mergePreferences(prev, patch));
  }, []);

  const patchPreferencesRemote = useCallback(async (patch: UserPreferencesPatch) => {
    if (!hasSessionToken()) {
      patchPreferencesLocal(patch);
      return;
    }
    setPreferences((prev) => mergePreferences(prev, patch));
    try {
      const next = await patchUserPreferences(patch);
      setPreferences(next);
    } catch {
      // Keep optimistic state to avoid disruptive UX in temporary network failures.
    }
  }, [patchPreferencesLocal]);

  const refresh = useCallback(async () => {
    if (!hasSessionToken()) {
      setSession(null);
      setPreferences(defaultUserPreferences());
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [me, prefs] = await Promise.all([getAuthMe(), getUserPreferences()]);
      setSession(me);
      setPreferences(prefs);
      if (typeof window !== "undefined") {
        const migrationMark = `${MIGRATION_MARK_PREFIX}:${me.user_id || me.sub || "default"}`;
        if (window.localStorage.getItem(migrationMark) === "true") {
          setLoading(false);
          return;
        }
        const legacyPatch = readLegacyPatch();
        const hasLegacy = Object.keys(legacyPatch).length > 0;
        if (hasLegacy) {
          const merged = mergePreferences(prefs, {
            ...legacyPatch,
            preferences_version: "v1.2.1",
          });
          const patched = await patchUserPreferences({
            ...legacyPatch,
            preferences_version: "v1.2.1",
            onboarding_ui: merged.onboarding_ui,
            tour_completed_modules: merged.tour_completed_modules,
          });
          setPreferences(patched);
        } else if (prefs.preferences_version !== "v1.2.1") {
          const patched = await patchUserPreferences({ preferences_version: "v1.2.1" });
          setPreferences(patched);
        }
        window.localStorage.setItem(migrationMark, "true");
      }
    } catch {
      setSession(null);
      setPreferences(defaultUserPreferences());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handleAuthStateChange = () => {
      void refresh();
    };
    window.addEventListener("storage", handleAuthStateChange);
    window.addEventListener("focus", handleAuthStateChange);
    window.addEventListener("socio-auth-changed", handleAuthStateChange);
    return () => {
      window.removeEventListener("storage", handleAuthStateChange);
      window.removeEventListener("focus", handleAuthStateChange);
      window.removeEventListener("socio-auth-changed", handleAuthStateChange);
    };
  }, [refresh]);

  const value = useMemo<UserPreferencesContextValue>(
    () => ({
      session,
      preferences,
      loading,
      refresh,
      patchPreferences: patchPreferencesRemote,
    }),
    [session, preferences, loading, refresh, patchPreferencesRemote],
  );

  return <UserPreferencesContext.Provider value={value}>{children}</UserPreferencesContext.Provider>;
}

export function useUserPreferences(): UserPreferencesContextValue {
  const ctx = useContext(UserPreferencesContext);
  if (!ctx) {
    return {
      session: null,
      preferences: defaultUserPreferences(),
      loading: false,
      refresh: async () => undefined,
      patchPreferences: async () => undefined,
    };
  }
  return ctx;
}
