import { CostTrendChart } from "@/components/analytics/CostTrendChart";
import { AlriTrendChart } from "@/components/analytics/AlriTrendChart";
import { ProviderCostChart } from "@/components/analytics/ProviderCostChart";
import { ProviderLatencyChart } from "@/components/analytics/ProviderLatencyChart";
import { ProviderRiskChart } from "@/components/analytics/ProviderRiskChart";
import { HeroSavingsCard } from "@/components/analytics/HeroSavingsCard";
import { ProviderContextLabels } from "@/components/analytics/ProviderContextLabels";
import { SavingsTrendChart } from "@/components/analytics/SavingsTrendChart";
import { RoutingEfficiencyCard } from "@/components/analytics/RoutingEfficiencyCard";
import { ProviderMixChart } from "@/components/analytics/ProviderMixChart";
import { CategoryDistributionChart } from "@/components/analytics/CategoryDistributionChart";

export default function AnalyticsPage() {
  return (
    <main className="min-h-screen w-full space-y-10 px-8 py-6">
      <section>
        <h1 className="text-3xl font-bold text-white">Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">
          Deeper cost and performance insights for your router.
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <HeroSavingsCard />
          <RoutingEfficiencyCard />
        </div>
        <div className="lg:col-span-2">
          <SavingsTrendChart />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <CostTrendChart />
        <AlriTrendChart />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div>
          <ProviderCostChart />
          <ProviderContextLabels />
        </div>
        <div>
          <ProviderLatencyChart />
          <ProviderContextLabels />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <ProviderMixChart />
        <CategoryDistributionChart />
      </section>

      <section>
        <ProviderRiskChart />
      </section>

      <section>
        <p className="text-xs text-slate-500">
          More charts and filters coming soon.
        </p>
      </section>
    </main>
  );
}
