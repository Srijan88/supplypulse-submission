"use client";

import {
  Activity,
  ArrowRight,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

type LoginScreenProps = {
  onLogin: () => void;
};

const DEMO_EMAIL = "demo@northbridge.energy";
const DEMO_PASSWORD = "northbridge123";

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (
      email.trim().toLowerCase() === DEMO_EMAIL &&
      password === DEMO_PASSWORD
    ) {
      localStorage.setItem("supplypulse_demo_auth", "true");
      onLogin();
      return;
    }

    setError("Invalid workspace credentials.");
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,#ede9fe_0,#f8fafc_35%,#ffffff_100%)]">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="flex items-center px-6 py-10 md:px-12 lg:px-16">
          <div className="max-w-2xl">
            <div className="mb-8 flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-xl shadow-violet-200">
                <Activity size={27} />
              </div>

              <div>
                <div className="text-2xl font-black tracking-tight text-slate-950">
                  SupplyPulse
                </div>
                <div className="text-sm text-slate-500">
                  Delivery Exposure Control Tower
                </div>
              </div>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-black text-violet-700 shadow-sm ring-1 ring-violet-100">
              <Sparkles size={15} />
              NorthBridge workspace ready
            </div>

            <h1 className="mt-6 text-4xl font-black tracking-tight text-slate-950 md:text-6xl">
              Monitor delivery exposure before delays become business impact.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-8 text-slate-600">
              SupplyPulse connects schedule exposure, geopolitical signals,
              trade / tariff evidence, route logistics exposure, source quality,
              reports, and audit trails into one enterprise workflow.
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-3">
              <FeatureCard title="Schedule" text="Delivery exposure table" />
              <FeatureCard title="Evidence" text="Source quality filtering" />
              <FeatureCard title="Audit" text="Traceable agent decisions" />
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center px-6 py-10 md:px-12">
          <div className="w-full max-w-md rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-2xl shadow-slate-200 backdrop-blur">
            <div className="mb-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-violet-50 text-violet-700">
                <ShieldCheck size={23} />
              </div>

              <h2 className="mt-5 text-2xl font-black text-slate-950">
                Sign in to workspace
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-500">
                Access the NorthBridge Energy Infrastructure workspace for the
                Singapore Data Center Phase 2 program.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block">
                <span className="text-xs font-black uppercase tracking-wide text-slate-500">
                  Email
                </span>

                <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <Mail size={18} className="text-slate-400" />
                  <input
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="w-full bg-transparent text-sm font-semibold text-slate-950 outline-none"
                    placeholder={DEMO_EMAIL}
                  />
                </div>
              </label>

              <label className="block">
                <span className="text-xs font-black uppercase tracking-wide text-slate-500">
                  Password
                </span>

                <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <Lock size={18} className="text-slate-400" />
                  <input
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    type="password"
                    className="w-full bg-transparent text-sm font-semibold text-slate-950 outline-none"
                    placeholder={DEMO_PASSWORD}
                  />
                </div>
              </label>

              {error && (
                <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700 ring-1 ring-rose-100">
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-3 text-sm font-black text-white shadow-lg shadow-violet-200 transition hover:from-violet-700 hover:to-indigo-700"
              >
                Enter NorthBridge Workspace
                <ArrowRight size={18} />
              </button>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}

function FeatureCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white/80 p-4 shadow-sm">
      <div className="text-sm font-black text-slate-950">{title}</div>
      <div className="mt-1 text-xs leading-5 text-slate-500">{text}</div>
    </div>
  );
}