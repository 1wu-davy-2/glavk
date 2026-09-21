import { useEffect, useRef, useState } from "react";
import { ExternalLink, MoreHorizontal, Star } from "lucide-react";

import type { WebProject } from "../types";

interface ProjectCardProps {
  project: WebProject;
  screenshotUrl?: string;
  /** 工作台的「当前焦点」用大卡片：标题压在封面上，星标移到状态行右侧。 */
  hero?: boolean;
  onCopy: () => void;
  onFavorite: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function formatUpdated(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚更新";
  return new Intl.DateTimeFormat("zh-CN", { month: "long", day: "numeric" }).format(date);
}

/** 列表里显示主机和端口就够了，完整地址放在 href 上。 */
export function formatHost(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/[/?#].*$/, "");
}

function credentialNote(project: WebProject): string {
  if (!project.has_credentials) return "公开页面，无需登录";
  if (!project.password_masked) return "只保存了登录用户名";
  return "凭证已加密保存在服务端";
}

export function ProjectCard({ project, screenshotUrl, hero = false, onCopy, onFavorite, onEdit, onDelete }: ProjectCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    const close = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setMenuOpen(false);
    };
    const escape = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false); };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", escape);
    };
  }, [menuOpen]);

  const runMenuAction = (action: () => void) => () => { setMenuOpen(false); action(); };

  const starButton = (
    <button
      className={`star-button ${project.is_favorite ? "is-favorite" : ""}`}
      type="button"
      aria-label={project.is_favorite ? "取消收藏" : "收藏项目"}
      title={project.is_favorite ? "取消收藏" : "收藏项目"}
      onClick={onFavorite}
    >
      <Star size={17} fill={project.is_favorite ? "currentColor" : "none"} />
    </button>
  );

  const statusChip = (
    <span className={`status-chip ${project.is_enabled ? "is-online" : "is-offline"}`}>
      <i /> {project.is_enabled ? "在线" : "已停用"}
    </span>
  );

  return (
    <article className={`project-card ${hero ? "is-hero" : ""} ${project.is_enabled ? "" : "is-disabled"}`}>
      <a className="project-cover" href={project.url} target="_blank" rel="noreferrer" aria-label={`打开 ${project.name}`}>
        {project.has_screenshot && screenshotUrl
          ? <img src={screenshotUrl} alt={`${project.name}网页截图`} />
          : <span className="cover-fallback">{project.name.slice(0, 1)}</span>}
        {hero && (
          <span className="cover-overlay">
            <small>{project.category}</small>
            <strong>{project.name}</strong>
          </span>
        )}
      </a>

      <div className="project-body">
        {hero ? (
          <div className="project-meta">
            {statusChip}
            <span className="project-category">{project.category}</span>
            {starButton}
          </div>
        ) : (
          <>
            <div className="project-head">
              <strong className="project-name">{project.name}</strong>
              {starButton}
            </div>
            <div className="project-meta">
              {statusChip}
              <span className="project-category">{project.category}</span>
            </div>
          </>
        )}

        <div className="project-host">{formatHost(project.url)}</div>

        <p className="project-note">
          {credentialNote(project)}{project.description ? ` · ${project.description}` : ""}
        </p>

        <footer className="project-foot">
          <button
            className="button button-primary button-small"
            type="button"
            onClick={() => window.open(project.url, "_blank", "noopener,noreferrer")}
          >
            <ExternalLink size={14} /> 打开系统
          </button>
          <span className="project-date">{formatUpdated(project.updated_at)}</span>

          <div className="card-menu" ref={menuRef}>
            <button
              className="icon-button"
              type="button"
              aria-label="更多操作"
              title="更多操作"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <MoreHorizontal size={17} />
            </button>
            {menuOpen && (
              <div className="card-menu-panel" role="menu">
                <button type="button" role="menuitem" onClick={runMenuAction(onEdit)}>编辑系统</button>
                <button type="button" role="menuitem" onClick={runMenuAction(onCopy)}>复制密码</button>
                <button type="button" role="menuitem" className="is-danger" onClick={runMenuAction(onDelete)}>删除系统</button>
              </div>
            )}
          </div>
        </footer>
      </div>
    </article>
  );
}
