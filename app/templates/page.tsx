"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "../../src/lib/api";
import NewTemplateModal from "./ui/NewTemplateModal";
import TemplateCard from "./ui/TemplateCard";
import TemplateRow from "./ui/TemplateRow";

type Template = {
  id: number | string;
  name: string;
  language: string;
  category: "MARKETING" | "UTILITY" | "AUTHENTICATION";
  subtype?: string | null;
  status: string;
  external_id?: string | null;
  rejection_reason?: string | null;
  quality_rating?: string | null;
  messaging_limit_tier?: string | null;
  is_paused?: boolean;
  source?: string;
  components?: any;
  created_at?: string;
  updated_at?: string;
};

function toResultsArray(data: any): any[] {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

const CATEGORY_LABELS: Record<string, string> = {
  ALL: "All categories",
  MARKETING: "Marketing",
  UTILITY: "Utility",
  AUTHENTICATION: "Authentication",
};

export default function TemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [category, setCategory] = useState<string>("ALL");
  const [language, setLanguage] = useState<string>("ALL");
  const [q, setQ] = useState<string>("");

  const [view, setView] = useState<"card" | "list">("card");
  const [isNewOpen, setIsNewOpen] = useState(false);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const data = await (api as any).listTemplates();
      setItems(toResultsArray(data) as Template[]);
    } catch (e: any) {
      setErr(e?.message || "Failed to load templates");
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
  }, []);

  const languages = useMemo(() => {
    const s = new Set<string>();
    items.forEach((t) => {
      if (t.language) s.add(t.language);
    });
    return ["ALL", ...Array.from(s).sort()];
  }, [items]);

  const filtered = useMemo(() => {
    let res = [...items];

    if (category !== "ALL") res = res.filter((t) => t.category === category);
    if (language !== "ALL") res = res.filter((t) => t.language === language);

    if (q.trim()) {
      const needle = q.trim().toLowerCase();
      res = res.filter((t) => {
        const hay = `${t.name} ${t.category} ${t.language} ${t.status} ${t.external_id || ""}`.toLowerCase();
        return hay.includes(needle);
      });
    }

    res.sort((a, b) => {
      const da = a.updated_at ? new Date(a.updated_at).getTime() : 0;
      const db = b.updated_at ? new Date(b.updated_at).getTime() : 0;
      return db - da;
    });

    return res;
  }, [items, category, language, q]);

  async function onCreate(payload: { name: string; category: string; language: string }) {
    const created = await (api as any).createTemplate({
      name: payload.name,
      category: payload.category,
      language: payload.language,
      components: { components: [{ type: "BODY", text: "Hi {{1}}," }] },
    });

    setItems((prev) => [created as any, ...prev]);
    setIsNewOpen(false);
  }

  async function onSubmit(id: string | number) {
    const updated = await (api as any).submitTemplate(id);
    setItems((prev) => prev.map((t) => (String(t.id) === String(id) ? (updated as any) : t)));
  }

  async function onSyncStatus(id: string | number) {
    const updated = await (api as any).syncTemplateStatus(id);
    setItems((prev) => prev.map((t) => (String(t.id) === String(id) ? (updated as any) : t)));
  }

  async function onDuplicate(tpl: Template) {
    const base = tpl.name.endsWith("_copy") ? tpl.name : `${tpl.name}_copy`;

    const created = await (api as any).createTemplate({
      name: base,
      category: tpl.category,
      language: tpl.language,
      components: tpl.components || { components: [{ type: "BODY", text: "Hi {{1}}," }] },
    });

    setItems((prev) => [created as any, ...prev]);
  }

  async function onDelete(id: string | number) {
    const ok = window.confirm("Delete this draft template? This cannot be undone.");
    if (!ok) return;

    await (api as any).deleteTemplate(id);
    setItems((prev) => prev.filter((t) => String(t.id) !== String(id)));
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-slate-900">Templates</h1>

        <button
          onClick={() => setIsNewOpen(true)}
          className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-sky-700"
        >
          + New template
        </button>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="ALL">{CATEGORY_LABELS.ALL}</option>
            <option value="MARKETING">{CATEGORY_LABELS.MARKETING}</option>
            <option value="UTILITY">{CATEGORY_LABELS.UTILITY}</option>
            <option value="AUTHENTICATION">{CATEGORY_LABELS.AUTHENTICATION}</option>
          </select>

          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="ALL">All languages</option>
            {languages
              .filter((x) => x !== "ALL")
              .map((lang) => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
          </select>

          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search templates..."
            className="min-w-[220px] flex-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />

          <div className="ml-auto flex items-center gap-1">
            <button
              onClick={() => setView("card")}
              className={`rounded-md border border-slate-200 px-2 py-1 ${
                view === "card" ? "bg-slate-100 text-slate-900" : "bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              Cards
            </button>
            <button
              onClick={() => setView("list")}
              className={`rounded-md border border-slate-200 px-2 py-1 ${
                view === "list" ? "bg-slate-100 text-slate-900" : "bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              List
            </button>

            <button
              onClick={load}
              className="rounded-md border border-slate-200 bg-white px-2 py-1 text-slate-700 hover:bg-slate-50"
              title="Reload"
            >
              Refresh
            </button>
          </div>
        </div>

        {err ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            <div className="font-semibold">Couldn’t load templates</div>
            <div className="mt-1 opacity-90">{err}</div>
          </div>
        ) : null}

        {loading ? (
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
            Loading templates…
          </div>
        ) : filtered.length === 0 ? (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
              <div className="mb-1 flex items-center justify-between">
                <span className="font-semibold text-slate-900">No templates yet</span>
                <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] uppercase text-slate-600">
                  Empty state
                </span>
              </div>
              <p className="text-slate-500">
                Once you sync from Meta or create templates here, you&apos;ll see previews, categories, and quality scores.
              </p>
            </div>
          </div>
        ) : view === "card" ? (
          <div className="grid gap-3 md:grid-cols-2">
            {filtered.map((t) => (
              <TemplateCard
                key={t.id}
                tpl={t}
                onSubmit={onSubmit}
                onSyncStatus={onSyncStatus}
                onDuplicate={onDuplicate}
                onDelete={onDelete}
              />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-md border border-slate-200">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 text-slate-600">
                <tr className="border-b">
                  <th className="px-3 py-2 text-left font-medium">Name</th>
                  <th className="px-3 py-2 text-left font-medium">Category</th>
                  <th className="px-3 py-2 text-left font-medium">Language</th>
                  <th className="px-3 py-2 text-left font-medium">Status</th>
                  <th className="px-3 py-2 text-left font-medium">Quality</th>
                  <th className="px-3 py-2 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <TemplateRow
                    key={t.id}
                    tpl={t}
                    onSubmit={onSubmit}
                    onSyncStatus={onSyncStatus}
                    onDuplicate={onDuplicate}
                    onDelete={onDelete}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <NewTemplateModal open={isNewOpen} onClose={() => setIsNewOpen(false)} onCreate={onCreate} />
    </div>
  );
}
