import { Copy, ExternalLink, MoreHorizontal, Pencil, Star, Trash2 } from "lucide-react";

import type { WebProject } from "../types";

interface ProjectCardProps {
  project: WebProject;
  screenshotUrl?: string;
  onCopy: () => void;
  onFavorite: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function formatUpdated(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚更新";
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit" }).format(date);
}

export function ProjectCard({ project, screenshotUrl, onCopy, onFavorite, onEdit, onDelete }: ProjectCardProps) {
  return <article className={`project-card ${project.is_enabled ? "" : "is-disabled"}`}>{project.has_screenshot && screenshotUrl && <div className="project-cover"><img src={screenshotUrl} alt={`${project.name}网页截图`} /></div>}<header className="project-card-header"><span className="project-avatar">{project.name.slice(0, 1)}</span><div className="project-title"><strong>{project.name}</strong><span>{project.category}</span></div><button className={`icon-button favorite-button ${project.is_favorite ? "is-favorite" : ""}`} type="button" aria-label={project.is_favorite ? "取消收藏" : "收藏项目"} title={project.is_favorite ? "取消收藏" : "收藏项目"} onClick={onFavorite}><Star size={17} fill={project.is_favorite ? "currentColor" : "none"} /></button></header><div className="project-status-row"><span className={`status-chip ${project.is_enabled ? "is-online" : "is-offline"}`}><i /> {project.is_enabled ? "正常" : "已停用"}</span><span className="project-updated">更新于 {formatUpdated(project.updated_at)}</span></div><a className="project-url" href={project.url} target="_blank" rel="noreferrer">{project.url.replace(/^https?:\/\//, "")}<ExternalLink size={13} /></a>{project.has_credentials ? project.password_masked ? <div className="credential-list"><div className="credential-row"><span>登录用户名</span><strong>{project.username || "凭据已加密"}</strong></div><div className="credential-row"><span>登录密码</span><div className="credential-value"><strong>{project.password_masked}</strong><button type="button" className="credential-icon" aria-label="复制密码" title="复制密码" onClick={onCopy}><Copy size={15} /></button></div></div></div> : <div className="credential-empty"><span>已配置登录信息</span><small>密码仅在复制时解密</small></div> : <div className="credential-empty"><span>无需登录</span><small>公开网页或静态系统</small></div>}<footer className="project-card-footer"><button className="button button-primary button-small" type="button" onClick={() => window.open(project.url, "_blank", "noopener,noreferrer")}><ExternalLink size={14} /> 打开系统</button><div className="card-actions"><button className="icon-button" type="button" aria-label="编辑系统" title="编辑系统" onClick={onEdit}><Pencil size={15} /></button><button className="icon-button" type="button" aria-label="更多操作" title="更多操作" onClick={onDelete}><MoreHorizontal size={16} /></button><button className="icon-button danger-button" type="button" aria-label="删除系统" title="删除系统" onClick={onDelete}><Trash2 size={15} /></button></div></footer></article>;
}
