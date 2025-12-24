"use client";

import { useRouter } from "next/navigation";

type Template = {
  id: number | string;
  name: string;
  category: string;
  language: string;
  status: string;
  quality_rating?: string | null;
  source?: string;
  external_id?: string | null;
};

type Props = {
  tpl: Template;
  onSubmit: (id: string | number) => void | Promise<void>;
  onSyncStatus: (id: string | number) => void | Promise<void>;
  onDuplicate?: (tpl: Template) => void | Promise<void>;
  onDelete?: (id: string | number) => void | Promise<void>;
};

export default function TemplateRow({
  tpl,
  onSubmit,
  onSyncStatus,
  onDuplicate,
  onDelete,
}: Props) {
  const router = useRouter();

  // ✅ MUST match backend destroy() rule exactly
  const canDelete =
    tpl.status === "DRAFT" &&
    tpl.source === "LOCAL" &&
    !tpl.external_id;

  const canSubmit = tpl.status === "DRAFT";

  async function handleDelete() {
    if (!canDelete) return;

    const ok = window.confirm("Delete this draft template? This cannot be undone.");
    if (!ok) return;

    await onDelete?.(tpl.id);
  }

  return (
    <tr className="border-b text-xs hover:bg-slate-50">
      <td className="px-3 py-2 font-medium">{tpl.name}</td>
      <td className="px-3 py-2">{tpl.category}</td>
      <td className="px-3 py-2">{tpl.language}</td>
      <td className="px-3 py-2">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase">
          {tpl.status}
        </span>
      </td>
      <td className="px-3 py-2">{tpl.quality_rating || "—"}</td>

      <td className="px-3 py-2 text-right whitespace-nowrap">
        <button
          onClick={() => router.push(`/templates/${tpl.id}`)}
          className="mr-2 text-sky-600 hover:underline"
        >
          Edit
        </button>

        <button
          onClick={() => onDuplicate?.(tpl)}
          className="mr-2 text-slate-700 hover:underline"
        >
          Duplicate
        </button>

        <button
          onClick={() => onSyncStatus(tpl.id)}
          className="mr-2 text-slate-700 hover:underline"
        >
          Refresh
        </button>

        <button
          onClick={() => canSubmit && onSubmit(tpl.id)}
          disabled={!canSubmit}
          className={`mr-2 ${
            canSubmit
              ? "text-sky-600 hover:underline"
              : "text-slate-400 cursor-not-allowed"
          }`}
          title={!canSubmit ? "Only DRAFT templates can be submitted" : ""}
        >
          Submit
        </button>

        {canDelete ? (
          <button
            onClick={handleDelete}
            className="text-rose-600 hover:underline"
          >
            Delete
          </button>
        ) : (
          <span
            className="text-slate-400 cursor-not-allowed"
            title="Only LOCAL DRAFT templates without Meta ID can be deleted"
          >
            Delete
          </span>
        )}
      </td>
    </tr>
  );
}
