export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type RequestOptions = RequestInit & {
  raw?: boolean; // if you ever want to read raw text
};

/**
 * Build absolute URL from relative API path
 */
function buildUrl(path: string) {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path}`;
}

/**
 * Read cookie value (used for CSRF token)
 */
function getCookie(name: string): string | undefined {
  if (typeof document === "undefined") return undefined;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(";").shift();
  }
}

/**
 * Core request wrapper
 */
async function request<T = any>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const url = buildUrl(path);

  // If body is FormData, do NOT set Content-Type
  const isFormData =
    typeof FormData !== "undefined" && options.body instanceof FormData;

  const method = (options.method || "GET").toUpperCase();
  const csrfToken = getCookie("csrftoken");

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      credentials: "include", // ✅ session auth
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),

        // ✅ CSRF token for unsafe methods
        ...(method !== "GET" && method !== "HEAD" && method !== "OPTIONS"
          ? { "X-CSRFToken": csrfToken || "" }
          : {}),

        ...(options.headers || {}),
      },
      cache: "no-store",
    });
  } catch (err: any) {
    throw new Error(
      `Network error calling ${url}. Is backend running? ${err?.message || ""}`
    );
  }

  // Handle non-OK responses
  if (!res.ok) {
    const contentType = res.headers.get("content-type") || "";
    let detail = "";

    try {
      if (contentType.includes("application/json")) {
        const j = await res.json();
        detail = typeof j === "string" ? j : JSON.stringify(j);
      } else {
        detail = await res.text();
      }
    } catch {
      detail = "Unknown error body";
    }

    throw new Error(`API error ${res.status}: ${detail}`);
  }

  if (options.raw) {
    return (await res.text()) as T;
  }

  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

/**
 * Bootstrap CSRF cookie (call once on app load)
 */
async function initCsrf() {
  await request("/api/core/csrf/");
}

export const api = {
  // =========================
  // Core
  // =========================
  initCsrf,

  // =========================
  // WhatsApp Accounts (READ)
  // =========================
  listWabas: () => request("/api/whatsapp/wabas/"),
  listPhoneNumbers: () => request("/api/whatsapp/phone-numbers/"),
  listQrCodes: () => request("/api/whatsapp/qr-codes/"),

  // =========================
  // Phone Number Actions
  // =========================
  registerNumber: (id: string, pin: string) =>
    request(`/api/whatsapp/phone-numbers/${id}/register/`, {
      method: "POST",
      body: JSON.stringify({ pin }),
    }),

  enableTwoStep: (id: string, pin: string) =>
    request(`/api/whatsapp/phone-numbers/${id}/enable_two_step/`, {
      method: "POST",
      body: JSON.stringify({ pin }),
    }),

  getProfile: (id: string) =>
    request(`/api/whatsapp/phone-numbers/${id}/profile/`),

  updateProfile: (id: string, data: any) =>
    request(`/api/whatsapp/phone-numbers/${id}/update_profile/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // =========================
  // QR Code Actions
  // =========================
  createQrCode: (payload: any) =>
    request("/api/whatsapp/qr-codes/create_for_number/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteQrCode: (id: string) =>
    request(`/api/whatsapp/qr-codes/${id}/`, { method: "DELETE" }),

  // =========================
  // Sync Actions (Meta)
  // =========================
  syncWabasFromMeta: () =>
    request("/api/whatsapp/wabas/sync_from_meta/", { method: "POST" }),

  syncPhoneNumbersForWaba: (wabaDbId: string) =>
    request(`/api/whatsapp/wabas/${wabaDbId}/sync_phone_numbers/`, {
      method: "POST",
    }),

  // =========================
  // Contacts
  // =========================
  listContacts: ({ q = "", page = 1 }: { q?: string; page?: number } = {}) => {
    const params = new URLSearchParams();
    if (q) params.set("search", q);
    params.set("page", String(page));
    return request(`/api/contacts/contacts/?${params.toString()}`);
  },

  createContact: (payload: any) =>
    request("/api/contacts/contacts/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateContact: (id: string, payload: any) =>
    request(`/api/contacts/contacts/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteContact: (id: string) =>
    request(`/api/contacts/contacts/${id}/`, { method: "DELETE" }),

  importContactsCsv: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/api/contacts/contacts/import-csv/`, {
      method: "POST",
      body: form,
    });
  },

  exportContactsCsv: async () => {
    window.open(
      `${API_BASE}/api/contacts/contacts/export-csv/`,
      "_blank"
    );
  },

  // =========================
  // Inbox / Messaging
  // =========================
  listInboxConversations: ({ q = "" }: { q?: string } = {}) => {
    const params = new URLSearchParams();
    if (q) params.set("search", q);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request(`/api/messaging/inbox/conversations/${suffix}`);
  },

  listInboxMessages: ({ contactId }: { contactId: string | number }) => {
    const params = new URLSearchParams();
    params.set("contact", String(contactId));
    return request(`/api/messaging/inbox/messages/?${params.toString()}`);
  },

  sendInboxMessage: (payload: {
    contact_id: number;
    body_text: string;
  }) =>
    request(`/api/messaging/inbox/messages/send/`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  markInboxRead: ({ contact_id }: { contact_id: number }) =>
    request(`/api/messaging/inbox/messages/mark_read/`, {
      method: "POST",
      body: JSON.stringify({ contact_id }),
    }),

  // =========================
  // Templates (MVP)
  // =========================
  listTemplates: () => request("/api/templates/"),

  createTemplate: (payload: any) =>
    request("/api/templates/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateTemplate: (id: string | number, payload: any) =>
    request(`/api/templates/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  submitTemplate: (id: string | number) =>
    request(`/api/templates/${id}/submit/`, { method: "POST" }),

  syncTemplateStatus: (id: string | number) =>
    request(`/api/templates/${id}/sync_status/`, { method: "POST" }),

  getTemplate: (id: string | number) => request(`/api/templates/${id}/`),

  deleteTemplate: (id: string | number) =>
    request(`/api/templates/${id}/`, { method: "DELETE" }), 
};