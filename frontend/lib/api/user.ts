import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type SessionUser = {
  sub: string;
  user_id: string;
  display_name: string;
  role: string;
  org_id: string;
  allowed_clientes: string[];
};

export type UserPreferences = {
  learning_role: "junior" | "semi" | "senior" | "socio";
  tour_completed_modules: string[];
  tour_welcome_seen: boolean;
  onboarding_ui: {
    welcome_seen: boolean;
    dismissed: boolean;
    visited_modules_ui: string[];
  };
  preferences_version: string;
};

export type UserPreferencesPatch = Partial<{
  learning_role: UserPreferences["learning_role"];
  tour_completed_modules: string[];
  tour_welcome_seen: boolean;
  onboarding_ui: Partial<UserPreferences["onboarding_ui"]>;
  preferences_version: string;
}>;

const DEFAULT_PREFERENCES: UserPreferences = {
  learning_role: "semi",
  tour_completed_modules: [],
  tour_welcome_seen: false,
  onboarding_ui: {
    welcome_seen: false,
    dismissed: false,
    visited_modules_ui: [],
  },
  preferences_version: "v1.2.1",
};

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((x) => String(x)).filter((x) => Boolean(x.trim())) : [];
}

export async function getAuthMe(): Promise<SessionUser> {
  const response = await authFetchJson<ApiEnvelope<unknown>>("/auth/me");
  const raw = asRecord(response?.data);
  return {
    sub: String(raw.sub ?? ""),
    user_id: String(raw.user_id ?? ""),
    display_name: String(raw.display_name ?? raw.sub ?? ""),
    role: String(raw.role ?? "auditor"),
    org_id: String(raw.org_id ?? ""),
    allowed_clientes: asStringArray(raw.allowed_clientes),
  };
}

export async function getUserPreferences(): Promise<UserPreferences> {
  const response = await authFetchJson<ApiEnvelope<unknown>>("/api/user/preferences");
  const raw = asRecord(response?.data);
  const onboarding = asRecord(raw.onboarding_ui);
  const learning = String(raw.learning_role ?? DEFAULT_PREFERENCES.learning_role).toLowerCase();
  const learning_role =
    learning === "junior" || learning === "semi" || learning === "senior" || learning === "socio"
      ? (learning as UserPreferences["learning_role"])
      : DEFAULT_PREFERENCES.learning_role;
  return {
    learning_role,
    tour_completed_modules: asStringArray(raw.tour_completed_modules),
    tour_welcome_seen: Boolean(raw.tour_welcome_seen),
    onboarding_ui: {
      welcome_seen: Boolean(onboarding.welcome_seen),
      dismissed: Boolean(onboarding.dismissed),
      visited_modules_ui: asStringArray(onboarding.visited_modules_ui),
    },
    preferences_version: String(raw.preferences_version ?? DEFAULT_PREFERENCES.preferences_version),
  };
}

export async function patchUserPreferences(patch: UserPreferencesPatch): Promise<UserPreferences> {
  const response = await authFetchJson<ApiEnvelope<unknown>>("/api/user/preferences", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  const raw = asRecord(response?.data);
  const onboarding = asRecord(raw.onboarding_ui);
  const learning = String(raw.learning_role ?? DEFAULT_PREFERENCES.learning_role).toLowerCase();
  const learning_role =
    learning === "junior" || learning === "semi" || learning === "senior" || learning === "socio"
      ? (learning as UserPreferences["learning_role"])
      : DEFAULT_PREFERENCES.learning_role;
  return {
    learning_role,
    tour_completed_modules: asStringArray(raw.tour_completed_modules),
    tour_welcome_seen: Boolean(raw.tour_welcome_seen),
    onboarding_ui: {
      welcome_seen: Boolean(onboarding.welcome_seen),
      dismissed: Boolean(onboarding.dismissed),
      visited_modules_ui: asStringArray(onboarding.visited_modules_ui),
    },
    preferences_version: String(raw.preferences_version ?? DEFAULT_PREFERENCES.preferences_version),
  };
}

export function defaultUserPreferences(): UserPreferences {
  return {
    learning_role: DEFAULT_PREFERENCES.learning_role,
    tour_completed_modules: [...DEFAULT_PREFERENCES.tour_completed_modules],
    tour_welcome_seen: DEFAULT_PREFERENCES.tour_welcome_seen,
    onboarding_ui: {
      welcome_seen: DEFAULT_PREFERENCES.onboarding_ui.welcome_seen,
      dismissed: DEFAULT_PREFERENCES.onboarding_ui.dismissed,
      visited_modules_ui: [...DEFAULT_PREFERENCES.onboarding_ui.visited_modules_ui],
    },
    preferences_version: DEFAULT_PREFERENCES.preferences_version,
  };
}

