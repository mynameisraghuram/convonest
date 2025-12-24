"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

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
};

type Props = {
  tpl: Template;
  onSubmit: (id: string | number) => Promise<void> | void;
  onSyncStatus: (id: string | number) => Promise<void> | void;
  onDuplicate?: (tpl: Template) => void;
  onDelete?: (id: string | number) => void;
};

function renderTemplatePreview(text: string) {
  return text.replace(/\{\{\s*(\d+)\s*\}\}/g, (_m, n) => `[var${n}]`);
}

function getBodyText(components: any): string {
  const comps = Array.isArray(components) ? components : components?.components || [];
  const body = comps.find((c: any) => (c?.type || "").toUpperCase() === "BODY");
  return body?.text || "";
}

export default function TemplateCard({
  tpl,
  onSubmit,
  onSyncStatus,
  onDuplicate,
  onDelete,
}: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState<"submit" | "sync" | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const bodyText = useMemo(() => getBodyText(tpl.components), [tpl.components]);
  const preview = useMemo(() => renderTemplatePreview(bodyText), [bodyText]);

  // ✅ MUST match backend destroy() rule
  const canDelete = tpl.status === "DRAFT" && tpl.source === "LOCAL" && !tpl.external_id;

  async function handle(action: "submit" | "sync") {
    setBusy(action);
    try {
      action === "submit" ? await onSubmit(tpl.id) : await onSyncStatus(tpl.id);
    } finally {
      setBusy(null);
    }
  }

  function closeMenu() {
    setMenuOpen(false);
  }

  function handleEdit() {
    closeMenu();
    router.push(`/templates/${tpl.id}`);
  }

  async function handleDuplicate() {
    closeMenu();
    await onDuplicate?.(tpl);
  }

  async function handleDelete() {
    closeMenu();

    if (!canDelete) return;

    const ok = window.confirm("Delete this draft template? This cannot be undone.");
    if (!ok) return;

    await onDelete?.(tpl.id);
  }

  return (
    <div className="relative rounded-md border border-slate-200 bg-white p-3 text-xs shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-semibold text-slate-900">{tpl.name}</div>
          <div className="text-[11px] text-slate-500">
            {tpl.category} • {tpl.language} • {tpl.source}
          </div>
        </div>

        <div className="flex items-center gap-1">
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase">
            {tpl.status}
          </span>

          {/* More menu */}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="rounded px-1 text-slate-500 hover:bg-slate-100"
            aria-label="Template actions"
          >
            ⋯
          </button>
        </div>
      </div>

      {/* Actions dropdown */}
      {menuOpen && (
        <div className="absolute right-2 top-8 z-10 w-36 rounded-md border bg-white shadow">
          <button
            onClick={handleEdit}
            className="block w-full px-3 py-1.5 text-left hover:bg-slate-50"
          >
            Edit
          </button>

          <button
            onClick={handleDuplicate}
            className="block w-full px-3 py-1.5 text-left hover:bg-slate-50"
          >
            Duplicate
          </button>

          {canDelete ? (
            <button
              onClick={handleDelete}
              className="block w-full px-3 py-1.5 text-left text-rose-600 hover:bg-rose-50"
            >
              Delete
            </button>
          ) : (
            <div
              className="block w-full px-3 py-1.5 text-left text-slate-400 cursor-not-allowed"
              title="Only LOCAL DRAFT templates without Meta ID can be deleted"
            >
              Delete
            </div>
          )}
        </div>
      )}

      {/* Preview */}
      <div className="mt-2 rounded-md border bg-slate-50 p-2">
        <div className="mb-1 text-[11px] font-medium text-slate-600">Preview</div>
        <div className="whitespace-pre-wrap">{preview || "—"}</div>
      </div>

      {/* Meta info */}
      <div className="mt-2 text-[11px] text-slate-500">
        Quality: {tpl.quality_rating || "—"} • Meta ID: {tpl.external_id || "—"}
      </div>

      {/* Footer actions */}
      <div className="mt-3 flex justify-end gap-2">
        <button
          onClick={() => handle("sync")}
          disabled={busy !== null}
          className="rounded border px-2 py-1 hover:bg-slate-50 disabled:opacity-60"
        >
          {busy === "sync" ? "Refreshing…" : "Refresh"}
        </button>

        <button
          onClick={() => handle("submit")}
          disabled={busy !== null || tpl.status !== "DRAFT"}
          className="rounded bg-sky-600 px-2 py-1 text-white hover:bg-sky-700 disabled:opacity-60"
          title={tpl.status !== "DRAFT" ? "Only DRAFT templates can be submitted" : ""}
        >
          {busy === "submit" ? "Submitting…" : "Submit"}
        </button>
      </div>
    </div>
  );
}
