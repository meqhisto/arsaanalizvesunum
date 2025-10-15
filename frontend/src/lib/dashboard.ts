export type DashboardSummary = {
  total_analyses: number;
  total_contacts: number;
  total_deals: number;
  open_tasks: number;
  total_deal_value: number;
  last_analysis_at: string | null;
  dashboard_stats: {
    toplam_arsa_sayisi: number;
    ortalama_fiyat: number;
    en_yuksek_fiyat: number;
    en_dusuk_fiyat: number;
    toplam_deger: number;
    son_guncelleme: string | null;
  };
};

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const res = await fetch("/api/backend/v1/dashboard/summary", {
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error(`Dashboard summary request failed (${res.status})`);
  }

  const json = (await res.json()) as { data: DashboardSummary };
  return json.data;
}
