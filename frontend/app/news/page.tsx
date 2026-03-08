/* eslint-disable react/jsx-no-bind */
"use client";

import { type MouseEvent, useEffect, useState } from "react";

import { apiDelete, apiGet, apiPatch, apiPost } from "../../src/lib/api";
import { formatDateTime } from "../../src/lib/datetime";
import { useI18n } from "../../src/i18n";

type NewsStatus = "new" | "tracking" | "actioned" | "archived";

type NewsSource = {
  role: "primary" | "reference";
  url: string;
};

type NewsItem = {
  id: string;
  title: string;
  summary: string;
  opportunity: string;
  risk: string;
  tags: string[];
  status: NewsStatus;
  published_at: string;
  captured_at: string;
  raw_payload_json: Record<string, unknown>;
  sources: NewsSource[];
  created_at: string;
  updated_at: string;
};

type NewsList = {
  items: NewsItem[];
  page: number;
  page_size: number;
  total: number;
};

type NewsDraft = {
  title: string;
  summary: string;
  opportunity: string;
  risk: string;
  tags: string;
  status: NewsStatus;
  published_at: string;
  captured_at: string;
  primary_source_url: string;
  reference_urls: string;
  raw_payload_json: string;
};

function toDateTimeLocalValue(value?: string): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offsetMs = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function fromDateTimeLocalValue(value: string): string | null {
  if (!value.trim()) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

function parseTags(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseReferenceUrls(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname || url;
  } catch {
    return url;
  }
}

function buildNewsDraft(news: NewsItem): NewsDraft {
  const primarySource = news.sources.find((source) => source.role === "primary")?.url || "";
  const references = news.sources.filter((source) => source.role === "reference").map((source) => source.url);
  return {
    title: news.title,
    summary: news.summary,
    opportunity: news.opportunity,
    risk: news.risk,
    tags: (news.tags || []).join(", "),
    status: news.status,
    published_at: toDateTimeLocalValue(news.published_at),
    captured_at: toDateTimeLocalValue(news.captured_at),
    primary_source_url: primarySource,
    reference_urls: references.join("\n"),
    raw_payload_json: JSON.stringify(news.raw_payload_json || {}, null, 2),
  };
}

export default function NewsPage() {
  const { t, lang } = useI18n();
  const [items, setItems] = useState<NewsItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<NewsItem | null>(null);

  const [statusFilter, setStatusFilter] = useState<NewsStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");

  const [detailDraft, setDetailDraft] = useState<NewsDraft | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void onRefreshList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void onRefreshList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, searchQuery]);

  function statusLabel(status: NewsStatus): string {
    return t(`news.status.${status}`);
  }

  function formatTime(value?: string): string {
    return formatDateTime(value, lang);
  }

  async function onLoadDetail(newsId: string) {
    const detail = await apiGet<NewsItem>(`/api/v1/news/${newsId}`);
    setSelectedDetail(detail);
    setDetailDraft(buildNewsDraft(detail));
  }

  async function onRefreshList(preferredId?: string | null) {
    setError("");
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: "1", page_size: "100" });
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (searchQuery.trim()) params.set("q", searchQuery.trim());
      const listed = await apiGet<NewsList>(`/api/v1/news?${params.toString()}`);
      const nextItems = listed.items || [];
      setItems(nextItems);
      const nextId =
        preferredId && nextItems.some((item) => item.id === preferredId)
          ? preferredId
          : selectedId && nextItems.some((item) => item.id === selectedId)
            ? selectedId
            : nextItems[0]?.id ?? null;
      setSelectedId(nextId);
      if (nextId) {
        await onLoadDetail(nextId);
      } else {
        setSelectedDetail(null);
        setDetailDraft(null);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function onSaveDetail() {
    if (!selectedDetail || !detailDraft) return;
    if (
      !detailDraft.title.trim() ||
      !detailDraft.summary.trim() ||
      !detailDraft.opportunity.trim() ||
      !detailDraft.risk.trim() ||
      !detailDraft.primary_source_url.trim()
    ) {
      setError(t("news.errValidation"));
      return;
    }

    const publishedAt = fromDateTimeLocalValue(detailDraft.published_at);
    const capturedAt = fromDateTimeLocalValue(detailDraft.captured_at);
    if (!publishedAt || !capturedAt) {
      setError(t("news.errDatetime"));
      return;
    }

    let rawPayload: Record<string, unknown>;
    try {
      rawPayload = detailDraft.raw_payload_json.trim() ? JSON.parse(detailDraft.raw_payload_json) : {};
    } catch {
      setError(t("news.errRawPayload"));
      return;
    }

    const sources: NewsSource[] = [
      { role: "primary", url: detailDraft.primary_source_url.trim() },
      ...parseReferenceUrls(detailDraft.reference_urls).map((url) => ({ role: "reference" as const, url })),
    ];

    setError("");
    setNotice("");
    setLoading(true);
    try {
      await apiPatch<NewsItem>(`/api/v1/news/${selectedDetail.id}`, {
        title: detailDraft.title.trim(),
        summary: detailDraft.summary.trim(),
        opportunity: detailDraft.opportunity.trim(),
        risk: detailDraft.risk.trim(),
        tags: parseTags(detailDraft.tags),
        status: detailDraft.status,
        published_at: publishedAt,
        captured_at: capturedAt,
        sources,
        raw_payload_json: rawPayload,
      });
      setNotice(t("news.noticeUpdated"));
      await onRefreshList(selectedDetail.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function onArchiveSelected() {
    if (!selectedDetail) return;
    setError("");
    setNotice("");
    setLoading(true);
    try {
      await apiPost<NewsItem>(`/api/v1/news/${selectedDetail.id}/archive`, {});
      setNotice(t("news.noticeArchived"));
      await onRefreshList(selectedDetail.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function deleteNews(newsId: string, preferredNextId?: string | null) {
    setError("");
    setNotice("");
    setLoading(true);
    try {
      await apiDelete(`/api/v1/news/${newsId}`);
      setNotice(t("news.noticeDeleted"));
      await onRefreshList(preferredNextId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function onDeleteSelected() {
    if (!selectedDetail) return;
    if (!window.confirm(t("news.confirmDelete"))) return;
    const currentIndex = items.findIndex((item) => item.id === selectedDetail.id);
    const preferredNextId = items[currentIndex + 1]?.id || items[currentIndex - 1]?.id || null;
    await deleteNews(selectedDetail.id, preferredNextId);
  }

  async function onDeleteFromList(event: MouseEvent<HTMLButtonElement>, newsId: string) {
    event.stopPropagation();
    if (!window.confirm(t("news.confirmDelete"))) return;
    const currentIndex = items.findIndex((item) => item.id === newsId);
    const preferredNextId =
      selectedId === newsId ? items[currentIndex + 1]?.id || items[currentIndex - 1]?.id || null : selectedId;
    await deleteNews(newsId, preferredNextId);
  }

  return (
    <section className="card newsBoard">
      <div className="newsHero">
        <div>
          <h1 className="h1">{t("news.title")}</h1>
          <p className="meta">{t("news.subtitle")}</p>
        </div>
        <div className="newsHeroFilters">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t("news.searchPlaceholder")}
            className="taskInput"
          />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as NewsStatus | "all")} className="taskInput">
            <option value="all">{t("news.status.all")}</option>
            <option value="new">{t("news.status.new")}</option>
            <option value="tracking">{t("news.status.tracking")}</option>
            <option value="actioned">{t("news.status.actioned")}</option>
            <option value="archived">{t("news.status.archived")}</option>
          </select>
        </div>
      </div>

      {error ? <p className="meta" style={{ color: "var(--danger)" }}>{error}</p> : null}
      {notice ? <p className="meta" style={{ color: "var(--success)" }}>{notice}</p> : null}

      <div className="newsLayout">
        <div className="newsListPanel">
          <div className="newsList">
            {items.map((item) => {
              const primarySource = item.sources.find((source) => source.role === "primary")?.url || "";
              return (
                <div
                  key={item.id}
                  className={`knowledgeRow newsListRow ${selectedId === item.id ? "knowledgeRowActive" : ""}`}
                  onClick={() => {
                    setSelectedId(item.id);
                    void onLoadDetail(item.id);
                  }}
                >
                  <div className="knowledgeRowMain">
                    <div className="knowledgeTitle">
                      <span className="badge" style={{ marginRight: 8 }}>{statusLabel(item.status)}</span>
                      {item.title}
                    </div>
                    <div className="newsRowMeta">
                      <span>{t("news.publishedAt")}: {formatTime(item.published_at)}</span>
                      <span>{t("news.capturedAt")}: {formatTime(item.captured_at)}</span>
                      <span>{hostnameOf(primarySource) || "-"}</span>
                      <span>{(item.tags || []).join(", ") || "-"}</span>
                    </div>
                  </div>
                  <button className="badge newsListDeleteButton" onClick={(event) => void onDeleteFromList(event, item.id)} disabled={loading}>
                    {t("news.delete")}
                  </button>
                </div>
              );
            })}
            {!items.length ? <p className="meta">{loading ? t("news.loading") : t("news.emptyList")}</p> : null}
          </div>
        </div>

        <aside className="knowledgeDetail">
          <h2 className="changesSubTitle">{t("news.detail")}</h2>
          {selectedDetail && detailDraft ? (
            <div className="knowledgeDetailContent">
              <div className="knowledgeDetailTitle">{selectedDetail.title}</div>
              <div className="meta">{selectedDetail.id}</div>

              <div className="taskDetailGrid">
                <div>
                  <div className="changesSummaryKey">{t("news.updated")}</div>
                  <div className="changesLedgerText">{formatTime(selectedDetail.updated_at)}</div>
                </div>
                <div>
                  <div className="changesSummaryKey">{t("news.sourceCount")}</div>
                  <div className="changesLedgerText">{selectedDetail.sources.length}</div>
                </div>
              </div>

              <div className="knowledgeEdit">
                <div className="taskDetailFormGrid">
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.title")}</span>
                    <input
                      value={detailDraft.title}
                      onChange={(e) => setDetailDraft({ ...detailDraft, title: e.target.value })}
                      className="taskInput"
                    />
                  </label>
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.summary")}</span>
                    <textarea
                      value={detailDraft.summary}
                      onChange={(e) => setDetailDraft({ ...detailDraft, summary: e.target.value })}
                      className="taskInput taskTextArea"
                      rows={4}
                    />
                  </label>
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.opportunity")}</span>
                    <textarea
                      value={detailDraft.opportunity}
                      onChange={(e) => setDetailDraft({ ...detailDraft, opportunity: e.target.value })}
                      className="taskInput taskTextArea"
                      rows={4}
                    />
                  </label>
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.risk")}</span>
                    <textarea
                      value={detailDraft.risk}
                      onChange={(e) => setDetailDraft({ ...detailDraft, risk: e.target.value })}
                      className="taskInput taskTextArea"
                      rows={4}
                    />
                  </label>
                  <label className="taskField">
                    <span>{t("news.field.status")}</span>
                    <select
                      value={detailDraft.status}
                      onChange={(e) => setDetailDraft({ ...detailDraft, status: e.target.value as NewsStatus })}
                      className="taskInput"
                    >
                      <option value="new">{t("news.status.new")}</option>
                      <option value="tracking">{t("news.status.tracking")}</option>
                      <option value="actioned">{t("news.status.actioned")}</option>
                      <option value="archived">{t("news.status.archived")}</option>
                    </select>
                  </label>
                  <label className="taskField">
                    <span>{t("news.field.tags")}</span>
                    <input
                      value={detailDraft.tags}
                      onChange={(e) => setDetailDraft({ ...detailDraft, tags: e.target.value })}
                      className="taskInput"
                      placeholder="ai, robotics"
                    />
                  </label>
                  <label className="taskField">
                    <span>{t("news.field.publishedAt")}</span>
                    <input
                      type="datetime-local"
                      value={detailDraft.published_at}
                      onChange={(e) => setDetailDraft({ ...detailDraft, published_at: e.target.value })}
                      className="taskInput"
                    />
                  </label>
                  <label className="taskField">
                    <span>{t("news.field.capturedAt")}</span>
                    <input
                      type="datetime-local"
                      value={detailDraft.captured_at}
                      onChange={(e) => setDetailDraft({ ...detailDraft, captured_at: e.target.value })}
                      className="taskInput"
                    />
                  </label>
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.primarySource")}</span>
                    <input
                      value={detailDraft.primary_source_url}
                      onChange={(e) => setDetailDraft({ ...detailDraft, primary_source_url: e.target.value })}
                      className="taskInput"
                    />
                  </label>
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.referenceSources")}</span>
                    <textarea
                      value={detailDraft.reference_urls}
                      onChange={(e) => setDetailDraft({ ...detailDraft, reference_urls: e.target.value })}
                      className="taskInput taskTextArea"
                      rows={4}
                    />
                  </label>
                  <label className="taskField taskFieldWide">
                    <span>{t("news.field.rawPayload")}</span>
                    <textarea
                      value={detailDraft.raw_payload_json}
                      onChange={(e) => setDetailDraft({ ...detailDraft, raw_payload_json: e.target.value })}
                      className="taskInput taskTextArea newsJsonField"
                      rows={8}
                    />
                  </label>
                </div>

                <div className="taskDetailFormActions">
                  <button className="badge" onClick={onSaveDetail} disabled={loading}>
                    {t("news.save")}
                  </button>
                  <button className="badge" onClick={onArchiveSelected} disabled={loading}>
                    {t("news.archive")}
                  </button>
                  <button className="badge" onClick={onDeleteSelected} disabled={loading}>
                    {t("news.delete")}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <p className="meta">{loading ? t("news.loading") : t("news.emptyDetail")}</p>
          )}
        </aside>
      </div>
    </section>
  );
}
