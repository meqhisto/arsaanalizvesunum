"use client";
import { useAuth } from "@/components/AuthProvider";
import { DashboardSummary, fetchDashboardSummary } from "@/lib/dashboard";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

export default function DashboardPage() {
  const { isAuthenticated, user, reload } = useAuth();
  const router = useRouter();
  const [metrics, setMetrics] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formatter = useMemo(() => new Intl.NumberFormat("tr-TR"), []);
  const currencyFormatter = useMemo(
    () => new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }),
    []
  );

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;

    let mounted = true;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const summary = await fetchDashboardSummary();
        if (mounted) setMetrics(summary);
      } catch (err) {
        if (mounted) setError((err as Error).message || "Veriler alınamadı");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    run();
    return () => {
      mounted = false;
    };
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <main className="min-h-screen p-8">Yönlendiriliyor...</main>;
  }

  return (
    <main className="min-h-screen p-8 space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-gray-600">
          Hoş geldiniz, {user?.ad} {user?.soyad}
        </p>
      </header>

      {loading && <p className="text-sm text-gray-500">Metrikler yükleniyor...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {metrics && (
        <section className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Toplam Analiz" value={formatter.format(metrics.total_analyses)} />
            <MetricCard label="Aktif Kişi" value={formatter.format(metrics.total_contacts)} />
            <MetricCard label="Fırsatlar" value={formatter.format(metrics.total_deals)} />
            <MetricCard label="Açık Görev" value={formatter.format(metrics.open_tasks)} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <MetricCard label="Toplam Fırsat Değeri" value={currencyFormatter.format(metrics.total_deal_value)} />
            <MetricCard
              label="Ortalama Analiz Fiyatı"
              value={currencyFormatter.format(metrics.dashboard_stats.ortalama_fiyat || 0)}
            />
            <MetricCard
              label="Portföy Toplam Değeri"
              value={currencyFormatter.format(metrics.dashboard_stats.toplam_deger || 0)}
            />
          </div>

          <div className="text-sm text-gray-600">
            {metrics.last_analysis_at ? (
              <p>Son analiz tarihi: {new Date(metrics.last_analysis_at).toLocaleString("tr-TR")}</p>
            ) : (
              <p>Henüz analiz bulunmuyor.</p>
            )}
            {metrics.dashboard_stats.son_guncelleme && (
              <p>İstatistikler güncelleme: {new Date(metrics.dashboard_stats.son_guncelleme).toLocaleString("tr-TR")}</p>
            )}
          </div>
        </section>
      )}
    </main>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}
