"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "../../../src/lib/api";

type Template = {
  id: number | string;
  name: string;
  language: string;
  category: "MARKETING" | "UTILITY" | "AUTHENTICATION";
  status: string;
  external_id?: string | null;
  rejection_reason?: string | null;
  quality_rating?: string | null;
  source?: string;
  components?: any;
  updated_at?: string;
};

type ButtonType = "QUICK_REPLY" | "URL" | "PHONE";
type TemplateButton = {
  type: ButtonType;
  text: string;
  url?: string;
  phone_number?: string;
};

function renderPreview(text: string) {
  if (!text) return "";
  return text.replace(/\{\{\s*(\d+)\s*\}\}/g, (_m, n) => `[var${n}]`);
}

function getComponentsArray(components: any): any[] {
  return Array.isArray(components)
    ? components
    : Array.isArray(components?.components)
    ? components.components
    : [];
}

function upsertComponent(components: any, type: string, patch: any) {
  const comps = [...getComponentsArray(components)];
  const t = type.toUpperCase();
  const idx = comps.findIndex((c: any) => (c?.type || "").toUpperCase() === t);

  if (idx >= 0) comps[idx] = { ...comps[idx], ...patch, type: t };
  else comps.push({ type: t, ...patch });

  return { components: comps };
}

function removeComponent(components: any, type: string) {
  const comps = getComponentsArray(components).filter(
    (c: any) => (c?.type || "").toUpperCase() !== type.toUpperCase()
  );
  return { components: comps };
}

function getBodyText(components: any): string {
  const comps = getComponentsArray(components);
  const body = comps.find((c: any) => (c?.type || "").toUpperCase() === "BODY");
  return body?.text || "";
}

function getHeaderText(components: any): string {
  const comps = getComponentsArray(components);
  const hdr = comps.find((c: any) => (c?.type || "").toUpperCase() === "HEADER");
  if (!hdr) return "";
  // For TEXT header: { type:"HEADER", format:"TEXT", text:"..." }
  return hdr?.text || "";
}

function getButtons(components: any): TemplateButton[] {
  const comps = getComponentsArray(components);
  const btnComp = comps.find((c: any) => (c?.type || "").toUpperCase() === "BUTTONS");
  const buttons = Array.isArray(btnComp?.buttons) ? btnComp.buttons : [];

  return buttons.map((b: any) => {
    const raw = (b?.type || "").toUpperCase();
    if (raw === "URL") return { type: "URL", text: b?.text || "", url: b?.url || "" };
    if (raw === "PHONE_NUMBER" || raw === "PHONE") return { type: "PHONE", text: b?.text || "", phone_number: b?.phone_number || "" };
    return { type: "QUICK_REPLY", text: b?.text || "" };
  });
}

function setButtons(components: any, buttons: TemplateButton[]) {
  if (!buttons || buttons.length === 0) return removeComponent(components, "BUTTONS");

  const normButtons = buttons.map((b) => {
    const t = (b.type || "QUICK_REPLY").toUpperCase();
    if (t === "URL") return { type: "URL", text: b.text || "", url: b.url || "" };
    if (t === "PHONE") return { type: "PHONE_NUMBER", text: b.text || "", phone_number: b.phone_number || "" };
    return { type: "QUICK_REPLY", text: b.text || "" };
  });

  return upsertComponent(components, "BUTTONS", { buttons: normButtons });
}

function isValidUrl(url: string) {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export default function TemplateEditPage() {
  const router = useRouter();
  const params = useParams();
  const id = (params?.id as string) || "";

  const [tpl, setTpl] = useState<Template | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<"save" | "submit" | "sync" | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [headerEnabled, setHeaderEnabled] = useState(false);
  const [headerText, setHeaderText] = useState("");

  const [bodyText, setBodyTextState] = useState("");
  const [buttons, setButtonsState] = useState<TemplateButton[]>([]);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const data = await (api as any).getTemplate(id);
      setTpl(data);

      const hdr = getHeaderText(data?.components);
      setHeaderEnabled(!!hdr);
      setHeaderText(hdr);

      setBodyTextState(getBodyText(data?.components));
      setButtonsState(getButtons(data?.components));
    } catch (e: any) {
      setErr(e?.message || "Failed to load template");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        await (api as any).initCsrf();
      } catch {}
      load();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const isDraft = tpl?.status === "DRAFT";
  const canEdit = !!tpl && isDraft;

  const previewHeader = useMemo(() => renderPreview(headerText), [headerText]);
  const previewBody = useMemo(() => renderPreview(bodyText), [bodyText]);

  async function saveDraft() {
    if (!tpl) return;
    setBusy("save");
    setErr(null);

    try {
      let newComponents = tpl.components;

      // Header
      if (headerEnabled && headerText.trim()) {
        newComponents = upsertComponent(newComponents, "HEADER", { format: "TEXT", text: headerText });
      } else {
        newComponents = removeComponent(newComponents, "HEADER");
      }

      // Body
      newComponents = upsertComponent(newComponents, "BODY", { text: bodyText });

      // Buttons
      newComponents = setButtons(newComponents, buttons);

      const updated = await (api as any).updateTemplate(tpl.id, {
        components: newComponents,
      });

      setTpl(updated);

      // refresh local state from backend response
      const hdr = getHeaderText(updated?.components);
      setHeaderEnabled(!!hdr);
      setHeaderText(hdr);
      setBodyTextState(getBodyText(updated?.components));
      setButtonsState(getButtons(updated?.components));
    } catch (e: any) {
      setErr(e?.message || "Failed to save");
    } finally {
      setBusy(null);
    }
  }

  async function submit() {
    if (!tpl) return;
    setBusy("submit");
    setErr(null);
    try {
      const updated = await (api as any).submitTemplate(tpl.id);
      setTpl(updated);
    } catch (e: any) {
      setErr(e?.message || "Submit failed");
    } finally {
      setBusy(null);
    }
  }

  async function syncStatus() {
    if (!tpl) return;
    setBusy("sync");
    setErr(null);
    try {
      const updated = await (api as any).syncTemplateStatus(tpl.id);
      setTpl(updated);
    } catch (e: any) {
      setErr(e?.message || "Refresh status failed");
    } finally {
      setBusy(null);
    }
  }

  function addButton(type: ButtonType) {
    if (!canEdit) return;

    // MVP limits: max 3 total; only 1 URL and 1 PHONE
    if (buttons.length >= 3) return;

    if (type === "URL" && buttons.some((b) => b.type === "URL")) return;
    if (type === "PHONE" && buttons.some((b) => b.type === "PHONE")) return;

    const base: TemplateButton =
      type === "URL"
        ? { type, text: "Visit", url: "https://example.com" }
        : type === "PHONE"
        ? { type, text: "Call", phone_number: "+911234567890" }
        : { type, text: "Reply" };

    setButtonsState((prev) => [...prev, base]);
  }

  function updateButton(i: number, patch: Partial<TemplateButton>) {
    if (!canEdit) return;
    setButtonsState((prev) => prev.map((b, idx) => (idx === i ? { ...b, ...patch } : b)));
  }

  function removeButton(i: number) {
    if (!canEdit) return;
    setButtonsState((prev) => prev.filter((_, idx) => idx !== i));
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => router.push("/templates")}
            className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
          >
            ← Back
          </button>
          <h1 className="text-lg font-semibold text-slate-900">Edit template</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={syncStatus}
            disabled={!tpl || busy !== null}
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            {busy === "sync" ? "Refreshing…" : "Refresh status"}
          </button>
          <button
            onClick={submit}
            disabled={!tpl || busy !== null || tpl.status !== "DRAFT"}
            className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-700 disabled:opacity-60"
            title={tpl?.status !== "DRAFT" ? "Only DRAFT templates can be submitted" : ""}
          >
            {busy === "submit" ? "Submitting…" : "Submit"}
          </button>
        </div>
      </div>

      {err ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          {err}
        </div>
      ) : null}

      {loading ? (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          Loading…
        </div>
      ) : !tpl ? (
        <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          Template not found.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Left */}
          <div className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3">
                <div className="text-sm font-semibold text-slate-900">{tpl.name}</div>
                <div className="mt-1 text-xs text-slate-500">
                  {tpl.category} • {tpl.language} • {tpl.source} •{" "}
                  <span className="font-medium">{tpl.status}</span>
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Meta ID: <span className="text-slate-700">{tpl.external_id || "—"}</span> • Quality:{" "}
                  <span className="text-slate-700">{tpl.quality_rating || "—"}</span>
                </div>
                {tpl.rejection_reason ? (
                  <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
                    <span className="font-semibold">Rejected:</span> {tpl.rejection_reason}
                  </div>
                ) : null}
              </div>

              {/* Header */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={headerEnabled}
                  onChange={(e) => setHeaderEnabled(e.target.checked)}
                  disabled={!canEdit}
                />
                <div className="text-xs font-medium text-slate-700">Enable Header (TEXT)</div>
              </div>

              {headerEnabled ? (
                <div className="mt-2">
                  <label className="block text-xs font-medium text-slate-700">Header</label>
                  <input
                    value={headerText}
                    onChange={(e) => setHeaderText(e.target.value)}
                    disabled={!canEdit}
                    className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                    placeholder="Header text (short)"
                  />
                </div>
              ) : null}

              {/* Body */}
              <label className="mt-3 block text-xs font-medium text-slate-700">Body</label>
              <textarea
                value={bodyText}
                onChange={(e) => setBodyTextState(e.target.value)}
                rows={8}
                disabled={!canEdit}
                className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                placeholder="Type your template body. Use {{1}}, {{2}} for variables."
              />

              <div className="mt-3 flex items-center justify-between">
                <div className="text-[11px] text-slate-500">
                  Variables: use <span className="font-mono">{"{{1}}"}</span>, <span className="font-mono">{"{{2}}"}</span>, …
                </div>

                <button
                  onClick={saveDraft}
                  disabled={busy !== null || !canEdit}
                  className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                  title={!canEdit ? "Only DRAFT templates can be edited. Duplicate to edit." : ""}
                >
                  {busy === "save" ? "Saving…" : "Save draft"}
                </button>
              </div>
            </div>

            {/* Buttons */}
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-sm font-semibold text-slate-900">Buttons</div>
                <div className="text-[11px] text-slate-500">Max 3 total • 1 URL • 1 Phone</div>
              </div>

              <div className="mb-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => addButton("QUICK_REPLY")}
                  disabled={!canEdit || buttons.length >= 3}
                  className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                >
                  + Quick reply
                </button>
                <button
                  type="button"
                  onClick={() => addButton("URL")}
                  disabled={!canEdit || buttons.length >= 3 || buttons.some((b) => b.type === "URL")}
                  className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                >
                  + URL
                </button>
                <button
                  type="button"
                  onClick={() => addButton("PHONE")}
                  disabled={!canEdit || buttons.length >= 3 || buttons.some((b) => b.type === "PHONE")}
                  className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                >
                  + Phone
                </button>
              </div>

              {buttons.length === 0 ? (
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                  No buttons yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {buttons.map((b, i) => {
                    const urlErr = b.type === "URL" && b.url && !isValidUrl(b.url);
                    const phoneErr =
                      b.type === "PHONE" &&
                      b.phone_number &&
                      !/^\+?[0-9]{8,15}$/.test((b.phone_number || "").replace(/\s+/g, ""));

                    return (
                      <div key={i} className="rounded-md border border-slate-200 bg-white p-3">
                        <div className="mb-2 flex items-center justify-between">
                          <div className="text-xs font-semibold text-slate-900">{b.type}</div>
                          <button
                            type="button"
                            onClick={() => removeButton(i)}
                            disabled={!canEdit}
                            className="text-xs text-rose-600 hover:underline disabled:opacity-60"
                          >
                            Remove
                          </button>
                        </div>

                        <label className="block text-[11px] font-medium text-slate-700">Label</label>
                        <input
                          value={b.text}
                          onChange={(e) => updateButton(i, { text: e.target.value.slice(0, 25) })}
                          disabled={!canEdit}
                          className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                          placeholder="Button label"
                        />

                        {b.type === "URL" ? (
                          <>
                            <label className="mt-2 block text-[11px] font-medium text-slate-700">URL</label>
                            <input
                              value={b.url || ""}
                              onChange={(e) => updateButton(i, { url: e.target.value })}
                              disabled={!canEdit}
                              className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                              placeholder="https://example.com"
                            />
                            {urlErr ? <div className="mt-1 text-[11px] text-rose-600">Enter a valid http/https URL.</div> : null}
                          </>
                        ) : null}

                        {b.type === "PHONE" ? (
                          <>
                            <label className="mt-2 block text-[11px] font-medium text-slate-700">Phone</label>
                            <input
                              value={b.phone_number || ""}
                              onChange={(e) => updateButton(i, { phone_number: e.target.value })}
                              disabled={!canEdit}
                              className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-sky-500 disabled:bg-slate-50"
                              placeholder="+911234567890"
                            />
                            {phoneErr ? (
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
          </div>

          {/* Right */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-2 text-xs font-semibold text-slate-900">Preview</div>

            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800 whitespace-pre-wrap">
              {headerEnabled && previewHeader ? (
                <>
                  <div className="mb-2 font-semibold">{previewHeader}</div>
                  <div className="mb-2 h-px bg-slate-200" />
                </>
              ) : null}
              {previewBody || "—"}
            </div>

            {buttons.length ? (
              <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
                <div className="mb-2 text-[11px] font-semibold text-slate-700">Buttons</div>
                <div className="flex flex-col gap-2">
                  {buttons.map((b, i) => (
                    <div
                      key={i}
                      className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700"
                    >
                      <span className="mr-2 rounded bg-white px-1 py-0.5 text-[10px] text-slate-500">{b.type}</span>
                      {b.text || "—"}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {!isDraft ? (
              <div className="mt-3 text-[11px] text-amber-700">
                This template is not a DRAFT. Editing is disabled for safety. Use “Duplicate” from Templates list to make an editable copy.
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
