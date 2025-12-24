"use client";

import { useState } from "react";
import { api } from "../../src/lib/api";

interface PhoneNumberCardProps {
  phone: any;
}

export default function PhoneNumberCard({ phone }: PhoneNumberCardProps) {
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);

  const canRun = pin.trim().length > 0 && !loading;

  async function handle(action: "register" | "two_step") {
    if (!pin.trim()) {
      alert("Please enter PIN");
      return;
    }

    setLoading(true);
    try {
      if (action === "register") {
        await api.registerNumber(phone.id, pin.trim());
        alert("Phone number registered successfully");
      } else {
        await api.enableTwoStep(phone.id, pin.trim());
        alert("Two-step verification enabled");
      }
    } catch (e: any) {
      alert(e?.message || "Action failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border border-slate-800 p-4 rounded-xl bg-slate-900/40 space-y-2">
      <div>
        <p className="font-semibold text-lg">
          {phone.display_name || "Unnamed"}{" "}
          <span className="text-sm text-slate-400">
            ({phone.e164_number || "no-number"})
          </span>
        </p>
        <p className="text-xs text-slate-500 mt-1">
          Phone Number ID: {phone.id}
        </p>
      </div>

      <div className="text-xs text-slate-400 space-y-1">
        <p>Registered: {phone.registered ? "Yes" : "No"}</p>
        <p>2FA: {phone.two_step_enabled ? "Enabled" : "Disabled"}</p>
        <p>Display name status: {phone.display_name_status || "-"}</p>
        <p>OBA status: {phone.oba_status || "-"}</p>
      </div>

      <div className="space-y-2 pt-2">
        <input
          type="password"
          placeholder="PIN for register / 2FA"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-sm"
        />

        <div className="flex gap-2">
          <button
            type="button"
            disabled={!canRun}
            onClick={() => handle("register")}
            className={`flex-1 text-sm py-1.5 rounded ${
              canRun
                ? "bg-emerald-600 hover:bg-emerald-500"
                : "bg-emerald-900/40 text-slate-400 cursor-not-allowed"
            }`}
          >
            {loading ? "Working..." : "Register"}
          </button>

          <button
            type="button"
            disabled={!canRun}
            onClick={() => handle("two_step")}
            className={`flex-1 text-sm py-1.5 rounded ${
              canRun
                ? "bg-blue-600 hover:bg-blue-500"
                : "bg-blue-900/40 text-slate-400 cursor-not-allowed"
            }`}
          >
            {loading ? "Working..." : "Enable 2FA"}
          </button>
        </div>
      </div>
    </div>
  );
}
