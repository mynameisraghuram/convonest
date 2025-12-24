"use client";

export default function Topbar() {
  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur">
      <div className="flex items-center gap-2">
        <span className="hidden text-sm font-medium text-slate-700 sm:inline">
          ConvoNest
        </span>
        <span className="hidden text-xs text-slate-400 sm:inline">
          • WhatsApp-first CRM
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500 sm:flex">
          <span className="mr-2 text-slate-400">⌕</span>
          <span className="opacity-80">Search contacts, templates...</span>
        </div>

        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-600 text-xs font-semibold text-white">
          SR
        </div>
      </div>
    </header>
  );
}
