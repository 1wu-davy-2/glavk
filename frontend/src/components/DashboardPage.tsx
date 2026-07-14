import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, ChevronDown, LayoutGrid, Plus, Search, ShieldCheck, Star, TriangleAlert } from "lucide-react";

import { createProject, deleteProject, listProjects, revealProjectCredential, updateProject } from "../api/client";
import type { AuthSession, ProjectPayload, WebProject } from "../types";
import { copyText } from "../utils/clipboard";
import { AppShell } from "./AppShell";
import { ProjectCard } from "./ProjectCard";
import { ProjectDrawer } from "./ProjectDrawer";
import { Toast } from "./Toast";

interface DashboardPageProps { session: AuthSession; onLogout: () => void; }

export function DashboardPage({ session, onLogout }: DashboardPageProps) {
  const [projects, setProjects] = useState<WebProject[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<WebProject | null>(null);
  const [revealedPasswords, setRevealedPasswords] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    setIsLoading(true); setError("");
    try { const result = await listProjects(search, category, favoriteOnly, session.accessToken); setProjects(result.items); setTotal(result.total); }
    catch (loadError) { setError(loadError instanceof Error ? loadError.message : "暂时无法加载系统列表"); }
    finally { setIsLoading(false); }
  }, [category, favoriteOnly, search, session.accessToken]);

  useEffect(() => { const timer = window.setTimeout(() => void refresh(), search ? 180 : 0); return () => window.clearTimeout(timer); }, [refresh, search]);
  useEffect(() => { if (!notice) return; const timer = window.setTimeout(() => setNotice(""), 3200); return () => window.clearTimeout(timer); }, [notice]);

  const categories = useMemo(() => Array.from(new Set(projects.map((project) => project.category).filter(Boolean))), [projects]);
  const enabledCount = projects.filter((project) => project.is_enabled).length;
  const favoriteCount = projects.filter((project) => project.is_favorite).length;

  const openCreate = () => { setEditingProject(null); setDrawerOpen(true); };
  const openEdit = (project: WebProject) => { setEditingProject(project); setDrawerOpen(true); };

  async function handleSave(payload: ProjectPayload) {
    if (editingProject) await updateProject(editingProject.id, payload, session.accessToken);
    else await createProject(payload, session.accessToken);
    setDrawerOpen(false); setNotice("系统已保存"); await refresh();
  }

  async function handleReveal(project: WebProject) {
    if (revealedPasswords[project.id]) { setRevealedPasswords((current) => { const next = { ...current }; delete next[project.id]; return next; }); return; }
    try { const result = await revealProjectCredential(project.id, session.accessToken); setRevealedPasswords((current) => ({ ...current, [project.id]: result.password })); }
    catch (revealError) { setError(revealError instanceof Error ? revealError.message : "密码查看失败"); }
  }

  async function handleCopy(project: WebProject) {
    const password = revealedPasswords[project.id];
    if (!password) return;
    try { if (await copyText(password)) setNotice("密码已复制"); else setError("当前浏览器不支持自动复制"); } catch { setError("当前浏览器不支持自动复制"); }
  }

  async function handleFavorite(project: WebProject) { try { await updateProject(project.id, { is_favorite: !project.is_favorite }, session.accessToken); await refresh(); } catch (updateError) { setError(updateError instanceof Error ? updateError.message : "更新失败"); } }

  async function handleDelete(project: WebProject) {
    if (!window.confirm(`确定删除“${project.name}”吗？删除后无法恢复。`)) return;
    try { await deleteProject(project.id, session.accessToken); setNotice("系统已删除"); await refresh(); } catch (deleteError) { setError(deleteError instanceof Error ? deleteError.message : "删除失败"); }
  }

  return <AppShell username={session.user.username} favoriteOnly={favoriteOnly} onShowAll={() => setFavoriteOnly(false)} onShowFavorites={() => setFavoriteOnly(true)} onLogout={onLogout}><div className="workspace-page"><section className="page-heading"><div><span className="eyebrow"><span className="live-dot" /> 管理中心</span><h1>网页系统</h1><p>集中管理所有业务入口与登录凭据</p></div><button className="button button-primary" type="button" onClick={openCreate}><Plus size={17} /> 添加系统</button></section><section className="metric-grid" aria-label="系统概览"><div className="metric-card"><span className="metric-icon blue"><ShieldCheck size={18} /></span><span><small>全部系统</small><strong>{total}</strong></span></div><div className="metric-card"><span className="metric-icon green"><Activity size={18} /></span><span><small>正常运行</small><strong>{enabledCount}</strong></span></div><div className="metric-card"><span className="metric-icon amber"><Star size={18} /></span><span><small>我的收藏</small><strong>{favoriteCount}</strong></span></div></section><section className="project-section"><div className="section-toolbar"><div><span className="eyebrow">系统目录</span><h2>{favoriteOnly ? "收藏项目" : "全部项目"}<span>{total.toString().padStart(2, "0")}</span></h2></div><div className="filter-tools"><label className="search-field"><Search size={16} /><span className="sr-only">搜索系统名称或地址</span><input aria-label="搜索系统名称或地址" placeholder="搜索系统名称或地址" value={search} onChange={(event) => setSearch(event.target.value)} /></label><label className="select-field"><span className="sr-only">按分类筛选</span><select aria-label="按分类筛选" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">全部分类</option>{categories.map((item) => <option key={item} value={item}>{item}</option>)}</select><ChevronDown size={14} /></label></div></div>{error && <div className="inline-error"><TriangleAlert size={16} /> {error}<button className="icon-button" type="button" aria-label="关闭错误" onClick={() => setError("")}>×</button></div>}{isLoading ? <div className="project-grid">{[1, 2, 3].map((item) => <div className="project-skeleton" key={item}><span /><span /><span /><span /></div>)}</div> : projects.length ? <div className="project-grid">{projects.map((project) => <ProjectCard key={project.id} project={project} revealedPassword={revealedPasswords[project.id]} onReveal={() => void handleReveal(project)} onCopy={() => void handleCopy(project)} onFavorite={() => void handleFavorite(project)} onEdit={() => openEdit(project)} onDelete={() => void handleDelete(project)} />)}</div> : <div className="empty-panel"><span className="empty-icon"><LayoutGrid size={22} /></span><span className="eyebrow">系统目录为空</span><h3>{search || category || favoriteOnly ? "没有匹配的系统" : "还没有网页系统"}</h3><p>{search || category || favoriteOnly ? "调整搜索或筛选条件后再试一次" : "添加你的第一个网页系统，开始建立统一入口"}</p>{!search && !category && !favoriteOnly && <button className="button button-primary" type="button" onClick={openCreate}><Plus size={16} /> 添加第一个系统</button>}</div>}</section></div><Toast message={notice} onDismiss={() => setNotice("")} /><ProjectDrawer open={drawerOpen} project={editingProject} onClose={() => setDrawerOpen(false)} onSave={handleSave} /></AppShell>;
}
