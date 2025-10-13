"use client";
import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardPage() {
  const { isAuthenticated, user, reload } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // ensure profile attempted
    reload();
  }, [reload]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return <main className="min-h-screen p-8">Yönlendiriliyor...</main>;
  }

  return (
    <main className="min-h-screen p-8 space-y-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="text-sm text-gray-600">Hoş geldiniz, {user?.ad} {user?.soyad}</p>
    </main>
  );
}
