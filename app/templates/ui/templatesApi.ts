async function request(path: string, init?: RequestInit) {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const msg =
      data?.detail ||
      data?.message ||
      `Request failed (${res.status})`;
    throw new Error(msg);
  }

  return data;
}

export const templatesApi = {
  list() {
    return request("/api/templates/");
  },
  create(payload: any) {
    return request("/api/templates/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  submit(id: string | number) {
    return request(`/api/templates/${id}/submit/`, { method: "POST" });
  },
  syncStatus(id: string | number) {
    return request(`/api/templates/${id}/sync_status/`, { method: "POST" });
  },
};
