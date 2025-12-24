export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Today&apos;s messages
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">
            0
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Inbound + outbound across all numbers.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Active contacts
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">
            0
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Contacts who messaged in the last 30 days.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Campaigns
          </div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">
            0
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Scheduled or running broadcasts.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">
            Recent activity
          </h2>
          <p className="mt-2 text-xs text-slate-500">
            Once webhooks are live, you&apos;ll see latest conversations here.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-800">
            Setup checklist
          </h2>
          <ul className="mt-2 space-y-1 text-xs text-slate-600">
            <li>• Connect your WhatsApp Business number</li>
            <li>• Import your first contact list</li>
            <li>• Create your first template</li>
            <li>• Send a test message</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
