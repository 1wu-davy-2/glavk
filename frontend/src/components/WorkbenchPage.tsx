import { ArrowUpRight, ExternalLink, LayoutGrid, Plus, TriangleAlert } from "lucide-react";

import type { WebProject } from "../types";
import { PageHeader } from "./PageHeader";
import { ProjectCard, formatHost } from "./ProjectCard";
import { StatBar } from "./StatBar";
import type { ProjectStats } from "./ProjectsPage";

interface WorkbenchPageProps {
  projects: WebProject[];
  stats: ProjectStats;
  focusId: string | null;
  onFocusChange: (id: string) => void;
  screenshotUrls: Record<string, string>;
  isLoading: boolean;
  error: string;
  onDismissError: () => void;
  onShowAll: () => void;
  onCreate: () => void;
  onCopy: (project: WebProject) => void;
  onFavorite: (project: WebProject) => void;
  onEdit: (project: WebProject) => void;
  onDelete: (project: WebProject) => void;
}

function todayLabel(): string {
  return new Intl.DateTimeFormat("zh-CN", { month: "long", day: "numeric", weekday: "long" }).format(new Date());
}

function entryHint(project: WebProject): string {
  if (!project.has_credentials) return `公开页面 · ${project.category}`;
  return `凭证已加密 · ${project.category}`;
}

export function WorkbenchPage({
  projects, stats, focusId, onFocusChange, screenshotUrls, isLoading, error, onDismissError,
  onShowAll, onCreate, onCopy, onFavorite, onEdit, onDelete,
}: WorkbenchPageProps) {
  const focus = projects.find((project) => project.id === focusId) ?? projects[0] ?? null;
  const others = projects.filter((project) => project.id !== focus?.id);

  return (
    <div className="workspace-page">
      <PageHeader
        eyebrow={todayLabel()}
        title="工作台"
        description="所有入口收在一处。点开即走，凭证加密保存在服务端。"
        action={<button className="button button-primary" type="button" onClick={onCreate}><Plus size={16} /> 添加系统</button>}
      />

      <StatBar total={stats.total} enabled={stats.enabled} favorites={stats.favorites} />

      {error && (
        <div className="inline-error" role="alert">
          <TriangleAlert size={16} /> {error}
          <button className="icon-button" type="button" aria-label="关闭错误" onClick={onDismissError}>×</button>
        </div>
      )}

      {isLoading ? (
        <div className="workbench-grid">
          <div className="project-skeleton" />
          <div className="project-skeleton" />
        </div>
      ) : focus ? (
        <div className="workbench-grid">
          <ProjectCard
            hero
            project={focus}
            screenshotUrl={screenshotUrls[focus.id]}
            onCopy={() => onCopy(focus)}
            onFavorite={() => onFavorite(focus)}
            onEdit={() => onEdit(focus)}
            onDelete={() => onDelete(focus)}
          />

          <aside className="side-panel">
            <div className="side-panel-head">
              <strong>其余入口</strong>
              <button className="link-button" type="button" onClick={onShowAll}>
                全部 <ArrowUpRight size={14} />
              </button>
            </div>

            <div className="entry-list">
              {others.length ? others.map((project) => (
                // 整行不是一个按钮：点中间切焦点，点右侧图标直接跳转，
                // 两个动作各自独立，所以用 div 包住两个 button。
                <div className="entry-item" key={project.id}>
                  <button
                    className="entry-main"
                    type="button"
                    aria-label={`在左侧查看 ${project.name}`}
                    onClick={() => onFocusChange(project.id)}
                  >
                    <span className="entry-thumb">
                      {project.has_screenshot && screenshotUrls[project.id]
                        ? <img src={screenshotUrls[project.id]} alt="" />
                        : project.name.slice(0, 1)}
                    </span>
                    <span className="entry-copy">
                      <strong>{project.name}</strong>
                      <small>{entryHint(project)}</small>
                    </span>
                  </button>
                  <span className="entry-actions">
                    <i className={`entry-dot ${project.is_enabled ? "is-online" : "is-offline"}`} />
                    <button
                      className="entry-open"
                      type="button"
                      aria-label={`跳转到 ${project.name}`}
                      title={`在新标签页打开 ${project.name}`}
                      onClick={() => window.open(project.url, "_blank", "noopener,noreferrer")}
                    >
                      <ArrowUpRight size={15} />
                    </button>
                  </span>
                </div>
              )) : <p className="entry-empty">还没有其它入口。</p>}
            </div>

            <div className="focus-block">
              <span className="eyebrow">当前焦点</span>
              <strong className="focus-host">{formatHost(focus.url)}</strong>
              <div className="focus-actions">
                <button
                  className="button button-primary button-small"
                  type="button"
                  onClick={() => window.open(focus.url, "_blank", "noopener,noreferrer")}
                >
                  <ExternalLink size={14} /> 打开
                </button>
                <button className="button button-ghost button-small" type="button" onClick={() => onEdit(focus)}>详情</button>
              </div>
            </div>
          </aside>
        </div>
      ) : (
        <div className="empty-panel">
          <span className="empty-icon"><LayoutGrid size={22} /></span>
          <span className="eyebrow">系统目录为空</span>
          <h3>还没有网页系统</h3>
          <p>添加你的第一个网页系统，开始建立统一入口</p>
          <button className="button button-primary" type="button" onClick={onCreate}><Plus size={16} /> 添加第一个系统</button>
        </div>
      )}
    </div>
  );
}
