"use client";

import { useEffect, useMemo, useState } from "react";

export type ButtonType = "QUICK_REPLY" | "URL" | "PHONE";

export type TemplateButton = {
  type: ButtonType;
  text: string;
  url?: string;
  phone_number?: string;
};

type Props = {
  value: TemplateButton[];
  onChange: (next: TemplateButton[]) => void;
  disabled?: boolean;
};

function clampText(s: string, max: number) {
  return (s || "").slice(0, max);
}

function isValidUrl(url: string) {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export default function TemplateButtonsEditor({ value, onChange, disabled }: Props) {
  const [rows, setRows] = useState<TemplateButton[]>(value || []);

  useEffect(() => {
    setRows(value || []);
  }, [value]);

  const quickReplyCount = useMemo(
    () => rows.filter((b) => b.type === "QUICK_REPLY").length,
    [rows]
  );

  const totalCount = rows.length;

  function commit(next: TemplateButton[]) {
    setRows(next);
    onChange(next);
  }

  function add(type: ButtonType) {
    if (disabled) return;

    // Conservative MVP limits:
    // - WhatsApp overall buttons (reply + CTA) have limits depending on layout.
    // We'll keep simple: max 3 total.
    if (totalCount >= 3) return;

    // Quick reply max 3; but also overall max 3, so this is fine.
    if (type === "QUICK_REPLY" && quickReplyCount >= 3) return;

    const base: TemplateButton =
      type === "URL"
        ? { type, text: "Visit", url: "https://example.com" }
        : type === "PHONE"
        ? { type, text: "Call", phone_number: "+911234567890" }
        : { type, text: "Reply" };

    commit([...rows, base]);
  }

  function remove(idx: number) {
    if (disabled) return;
    commit(rows.filter((_, i) => i !== idx));
  }

  function update(idx: number, patch: Partial<TemplateButton>) {
    if (disabled) return;
    const next = rows.map((b, i) => (i === idx ? { ...b, ...patch } : b));
    commit(next);
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-900">Buttons</div>
        <div className="text-[11px] text-slate-500">
          Max 3 total • Quick replies up to 3
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => add("QUICK_REPLY")}
          disabled={disabled || totalCount >= 3 || quickReplyCount >= 3}
          className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
        >
          + Quick reply
        </button>

        <button
          type="button"
          onClick={() => add("URL")}
          disabled={disabled || totalCount >= 3 || rows.some((b) => b.type === "URL")}
          className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          title={rows.some((b) => b.type === "URL") ? "Only one URL button in MVP" : ""}
        >
          + URL
        </button>

        <button
          type="button"
          onClick={() => add("PHONE")}
          disabled={disabled || totalCount >= 3 || rows.some((b) => b.type === "PHONE")}
          className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          title={rows.some((b) => b.type === "PHONE") ? "Only one Phone button in MVP" : ""}
        >
          + Phone
        </button>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          No buttons. Add quick replies or a CTA.
        </div>
      ) : (
        <div className="space-y-3">
          {rows.map((b, idx) => {
            const title =
              b.type === "QUICK_REPLY"
                ? "Quick reply"
                : b.type === "URL"
                ? "URL button"
                : "Phone button";

            const labelLimit = 25; // Meta button text limit is typically small; keep safe.

            const showUrlError = b.type === "URL" && b.url && !isValidUrl(b.url);
            const showPhoneError =
              b.type === "PHONE" && b.phone_number && !/^\+?[0-9]{8,15}$/.test(b.phone_number.replace(/\s+/g, ""));

            return (
              <div key={idx} className="rounded-md border border-slate-200 bg-white p-3">
                <div className="mb-2 flex items-center justify-between">
                  <div className="text-xs font-semibold text-slate-900">{title}</div>
                  <button
                    type="button"
                    onClick={() => remove(idx)}
                    disabled={disabled}
                    className="text-xs text-rose-600 hover:underline disabled:opacity-60"
                  >
                    Remove
                  </button>
                </div>

                <label className="block text-[11px] font-medium text-slate-700">Label</label>
                <input
                  value={b.text || ""}
                  onChange={(e) => update(idx, { text: clampText(e.target.value, labelLimit) })}
                  disabled={disabled}
                  className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                  placeholder="Button label"
                />
                <div className="mt-1 text-[10px] text-slate-500">{(b.text || "").length}/{labelLimit}</div>

                {b.type === "URL" ? (
                  <>
                    <label className="mt-2 block text-[11px] font-medium text-slate-700">URL</label>
                    <input
                      value={b.url || ""}
                      onChange={(e) => update(idx, { url: e.target.value })}
                      disabled={disabled}
                      className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                      placeholder="https://example.com"
                    />
                    {showUrlError ? (
                      <div className="mt-1 text-[11px] text-rose-600">Enter a valid http/https URL.</div>
                    ) : null}
                  </>
                ) : null}

                {b.type === "PHONE" ? (
                  <>
                    <label className="mt-2 block text-[11px] font-medium text-slate-700">Phone</label>
                    <input
                      value={b.phone_number || ""}
                      onChange={(e) => update(idx, { phone_number: e.target.value })}
                      disabled={disabled}
                      className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                      placeholder="+911234567890"
                    />
                    {showPhoneError ? (
                      <div className="mt-1 text-[11px] text-rose-600">Use digits with optional + (8–15 digits).</div>
                    ) : null}
                  </>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
