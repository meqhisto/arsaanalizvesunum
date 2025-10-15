"use client";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";

export default function Home() {
  const { isAuthenticated, user } = useAuth();

  return (
    <main className="min-h-screen p-8 space-y-6 bg-slate-950 text-slate-100">
      <div className="space-y-2">
        <p className="text-xs uppercase tracking-wide text-slate-400">Arsa Analiz ve Sunum</p>
        <h1 className="text-3xl font-semibold">Next.js Arayüzü 1.1.7</h1>
        <p className="text-sm text-slate-400">
          Yeni React tabanlı arayüzümüz kullanıma hazır. Dashboard ve CRM ekranları için giriş yapın.
        </p>
      </div>

      <section className="flex flex-wrap gap-3">
        <Link
          href="/dashboard"
          className="rounded-full bg-white text-slate-950 px-5 py-2 text-sm font-medium transition hover:bg-slate-200"
        >
          Dashboard
        </Link>
        {isAuthenticated ? (
          <span className="rounded-full border border-slate-700 px-5 py-2 text-sm text-slate-300">
            Oturum açık: {user?.ad} {user?.soyad}
          </span>
        ) : (
          <Link
            href="/login"
            className="rounded-full border border-slate-700 px-5 py-2 text-sm text-slate-200 transition hover:border-slate-500"
          >
            Giriş yap
          </Link>
        )}
      </section>

      <section className="space-y-2 text-sm text-slate-400">
        <p>Geliştirme notları:</p>
        <ul className="list-disc space-y-1 pl-4">
          <li>JWT erişim süresi dolarsa otomatik yenileme devrede.</li>
          <li>Dashboard sayfası backend özetini kartlar halinde gösteriyor.</li>
          <li>API çağrıları `/api/backend/*` üzerinden proxy'lenerek Flask ile konuşuyor.</li>
        </ul>
      </section>
    </main>
  );
}
