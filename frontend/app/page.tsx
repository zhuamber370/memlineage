"use client";

import { useI18n } from "../src/i18n";

export default function HomeDashboardPage() {
  const { t } = useI18n();

  return (
    <section className="card">
      <h1 className="h1">{t("home.title")}</h1>
      <p className="meta">{t("home.subtitle")}</p>
    </section>
  );
}
