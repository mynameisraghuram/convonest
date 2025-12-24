// frontend/app/settings/whatsapp/page.tsx

import PhoneNumberCard from "../../../components/whatsapp/PhoneNumberCard";
import CreateQrModal from "../../../components/whatsapp/CreateQrModal";
import QrCard from "../../../components/whatsapp/QrCard";
import SyncFromMetaButton from "../../../components/whatsapp/SyncFromMetaButton";
import SyncPhoneNumbersButton from "../../../components/whatsapp/SyncPhoneNumbersButton";
import StatusBadge from "../../../components/whatsapp/StatusBadge";
import { api } from "../../../src/lib/api";

function toArray(value: any): any[] {
  // Handles: [] OR {results: []} OR null/undefined OR {detail:"..."}
  if (Array.isArray(value)) return value;
  if (value && Array.isArray(value.results)) return value.results;
  return [];
}

export default async function WhatsAppSettingsPage() {
  let wabasRaw: any = null;
  let phoneNumbersRaw: any = null;
  let qrCodesRaw: any = null;
  let loadError: string | null = null;

  try {
    [wabasRaw, phoneNumbersRaw, qrCodesRaw] = await Promise.all([
      api.listWabas(),
      api.listPhoneNumbers(),
      api.listQrCodes(),
    ]);
  } catch (e: any) {
    loadError = e?.message || "Failed to load WhatsApp data";
  }

  const wabas = toArray(wabasRaw);
  const phoneNumbers = toArray(phoneNumbersRaw);
  const qrCodes = toArray(qrCodesRaw);

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">WhatsApp Accounts</h1>
          {loadError && <p className="mt-1 text-sm text-red-600">{loadError}</p>}
        </div>

        {/* ✅ IMPORTANT: No function props passed to client comps */}
        <div className="flex items-center gap-2">
          <SyncFromMetaButton />
          <CreateQrModal wabas={wabas} numbers={phoneNumbers} />
        </div>
      </div>

      {/* WABAs */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Business Accounts</h2>

        {wabas.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {wabas.map((w: any) => (
              <div
                key={w.id ?? `${w.name}-${Math.random()}`}
                className="border border-slate-800 p-4 rounded-xl bg-slate-900/40 space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold">{w.name || w.waba_id || w.id || "Unnamed WABA"}</p>
                  {/* ✅ shows Connected/Disconnected */}
                  <StatusBadge connected={!!w.is_connected} />
                </div>

                {/* Show both local DB id and Meta id (if present) */}
                <p className="text-xs text-slate-400">
                  DB ID: {w.id ?? "-"} | Meta WABA ID: {w.waba_id ?? w.id ?? "-"}
                </p>

                {w.meta_business_id && (
                  <p className="text-xs text-slate-500">
                    Meta Business ID: {w.meta_business_id}
                  </p>
                )}

                <div className="flex items-center justify-between gap-2 pt-1">
                  <p className="text-xs text-slate-500">
                    Last synced:{" "}
                    {w.last_synced_at
                      ? new Date(w.last_synced_at).toLocaleString()
                      : "-"}
                  </p>

                  {/* ✅ Sync Phone Numbers for this WABA (uses DB id) */}
                  {w.id && <SyncPhoneNumbersButton wabaDbId={String(w.id)} />}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
            No WhatsApp Business Accounts found
          </div>
        )}
      </section>

      {/* Phone Numbers */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Phone Numbers</h2>

        {phoneNumbers.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {phoneNumbers.map((p: any) => (
              <PhoneNumberCard
                key={p.id ?? `${p.e164_number}-${Math.random()}`}
                phone={p}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
            No phone numbers available
          </div>
        )}
      </section>

      {/* QR Codes */}
      <section>
        <h2 className="text-xl font-semibold mb-3">QR Codes</h2>

        {qrCodes.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-3">
            {qrCodes.map((qr: any) => (
              <QrCard
                key={qr.id ?? `${qr.name}-${Math.random()}`}
                qr={qr}
                onDelete={() => {
                  // QrCard itself calls router.refresh()
                }}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
            No QR codes created yet
          </div>
        )}
      </section>
    </div>
  );
}
