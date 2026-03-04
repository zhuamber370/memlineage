"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { apiGet } from "../lib/api";
import { useI18n } from "../i18n";

const PROPOSED_CHANGES_REFRESH_EVENT = "memlineage:proposed-changes-refresh";

const links = [
  { href: "/", key: "nav.home" },
  { href: "/tasks", key: "nav.tasks" },
  { href: "/knowledge", key: "nav.knowledge" },
  { href: "/changes", key: "nav.changes" },
  { href: "/skills", key: "nav.skills" }
] as const;

type ChangeCountResp = { total?: number };

export function AppShell({ children }: { children: ReactNode }) {
  const { lang, setLang, t } = useI18n();
  const [proposedChangeCount, setProposedChangeCount] = useState(0);

  useEffect(() => {
    let active = true;

    async function loadProposedCount() {
      try {
        const listed = await apiGet<ChangeCountResp>("/api/v1/changes?page=1&page_size=1&status=proposed");
        if (!active) return;
        setProposedChangeCount(typeof listed.total === "number" ? listed.total : 0);
      } catch {
        if (!active) return;
        setProposedChangeCount(0);
      }
    }

    void loadProposedCount();
    const onRefresh = () => {
      void loadProposedCount();
    };
    window.addEventListener(PROPOSED_CHANGES_REFRESH_EVENT, onRefresh);
    const timer = window.setInterval(() => {
      void loadProposedCount();
    }, 60000);
    return () => {
      active = false;
      window.removeEventListener(PROPOSED_CHANGES_REFRESH_EVENT, onRefresh);
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">MEMLINEAGE / AGENT-FIRST</div>
        <div className="badges" style={{ marginTop: 6, marginBottom: 10 }}>
          <button
            className="badge"
            onClick={() => setLang("en")}
            aria-pressed={lang === "en"}
            style={{ borderColor: lang === "en" ? "var(--focus)" : undefined }}
          >
            {t("lang.en")}
          </button>
          <button
            className="badge"
            onClick={() => setLang("zh")}
            aria-pressed={lang === "zh"}
            style={{ borderColor: lang === "zh" ? "var(--focus)" : undefined }}
          >
            {t("lang.zh")}
          </button>
        </div>
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`navLink ${link.href === "/changes" && proposedChangeCount > 0 ? "navLinkAlert" : ""}`}
          >
            <span className="navLinkInner">
              <span>{t(link.key)}</span>
              {link.href === "/changes" && proposedChangeCount > 0 ? (
                <span className="navLinkCount">{proposedChangeCount}</span>
              ) : null}
            </span>
          </Link>
        ))}
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
