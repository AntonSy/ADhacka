export type Level = "LOW" | "MEDIUM" | "HIGH";

export interface Match {
  rank: number;
  talk_id: string;
  title: string;
  conference_number: number;
  year: number;
  author: string;
  company: string | null;
  city: string | null;
  format: string | null;
  annotation: string | null;
  score: number;
  url: string | null;
  matched_aspects: string[];
}

export interface Check {
  id: string;
  status: string;
  level: Level;
  top_score: number;
  matches: Match[];
  recommendation: string | null;
  recommendation_source: string | null;
  annotation_hash: string;
  cached: boolean;
  created_at: string;
}

export interface Application {
  id: string;
  title: string;
  annotation: string;
  author_email: string;
  check_state: "checked" | "not_checked";
  level: Level | null;
  created_at: string;
}

export interface Talk {
  id: string;
  conference_number: number;
  title: string;
  annotation: string | null;
  author_name: string;
  company: string | null;
  source_url: string | null;
}

export interface Conference {
  number: number;
  year: number;
  talks_count: number;
}

export class ApiError extends Error {
  constructor(public status: number, public code: string, public retryAfter?: number) {
    super(code);
  }
}

export function sessionId(): string {
  let id = localStorage.getItem("ad_session");
  if (!id) {
    id = crypto.randomUUID().replace(/-/g, "");
    localStorage.setItem("ad_session", id);
  }
  return id;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  } catch {
    throw new ApiError(0, "NETWORK");
  }
  if (!res.ok) {
    let body: { error?: string; retry_after?: number } = {};
    try {
      body = await res.json();
    } catch {}
    throw new ApiError(res.status, body.error || "UNAVAILABLE", body.retry_after);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createCheck: (annotation: string, title?: string) =>
    request<Check>("/similarity-checks", {
      method: "POST",
      body: JSON.stringify({ annotation, title: title || null, session_id: sessionId() }),
    }),
  feedback: (id: string, useful: boolean, comment?: string) =>
    request<{ ok: boolean }>(`/similarity-checks/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ useful, comment: comment || null }),
    }),
  createApplication: (p: { title: string; annotation: string; email: string; check_id: string | null }) =>
    request<Application>("/applications", {
      method: "POST",
      body: JSON.stringify({ ...p, session_id: sessionId() }),
    }),
  applications: () => request<Application[]>(`/applications?session_id=${sessionId()}`),
  conferences: () => request<Conference[]>("/conferences"),
  talks: (params: { conference?: string; q?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params.conference && params.conference !== "all") qs.set("conference", params.conference);
    if (params.q) qs.set("q", params.q);
    qs.set("limit", String(params.limit ?? 100));
    qs.set("offset", String(params.offset ?? 0));
    return request<{ total: number; items: Talk[] }>(`/archive/talks?${qs}`);
  },
};

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    switch (e.code) {
      case "VALIDATION": return "Проверьте поля формы: аннотация должна содержать от 1 до 500 символов.";
      case "RATE_LIMIT": return `Лимит проверок исчерпан, повторите через ${Math.ceil((e.retryAfter ?? 600) / 60)} мин. Можно подать заявку без проверки.`;
      case "CHECK_OUTDATED": return "Аннотация изменилась после проверки. Перепроверьте её.";
      case "NETWORK": return "Нет соединения. Введённый текст сохранён, повторите попытку.";
      default: return "Сервис проверки недоступен. Повторите позже или подайте заявку без проверки.";
    }
  }
  return "Неизвестная ошибка.";
}
