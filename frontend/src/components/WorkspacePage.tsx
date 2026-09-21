import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { createProject, deleteProject, getProjectScreenshot, listProjects, revealProjectCredential, updateProject } from "../api/client";
import type { AuthSession, ProjectLayout, ProjectPayload, WebProject, WorkspaceView } from "../types";
import { copyText } from "../utils/clipboard";
import { loadDisplayName, saveDisplayName } from "../utils/preferences";
import { AppShell } from "./AppShell";
import { ProjectDrawer } from "./ProjectDrawer";
import { ProjectsPage } from "./ProjectsPage";
import { SettingsPage } from "./SettingsPage";
import { Toast } from "./Toast";
import { WorkbenchPage } from "./WorkbenchPage";

interface WorkspacePageProps {
  session: AuthSession;
  onLogout: () => void;
}

export function WorkspacePage({ session, onLogout }: WorkspacePageProps) {
  const [view, setView] = useState<WorkspaceView>("workbench");
  const [projects, setProjects] = useState<WebProject[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [layout, setLayout] = useState<ProjectLayout>("grid");
  const [focusId, setFocusId] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState(loadDisplayName);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<WebProject | null>(null);
  const [screenshotUrls, setScreenshotUrls] = useState<Record<string, string>>({});
  const screenshotUrlsRef = useRef<Record<string, string>>({});

  const refresh = useCallback(async () => {
    setIsLoading(true); setError("");
    try {
      // 一次取全量：指标卡和工作台都要看全局，搜索/分类/收藏都在前端筛。
      const result = await listProjects("", "", false, session.accessToken);
      setProjects(result.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "暂时无法加载系统列表");
    } finally {
      setIsLoading(false);
    }
  }, [session.accessToken]);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (!notice) return; const timer = window.setTimeout(() => setNotice(""), 3200); return () => window.clearTimeout(timer); }, [notice]);

  const visibleProjects = useMemo(() => {
    const term = search.trim().toLowerCase();
    return projects.filter((project) => {
      if (view === "favorites" && !project.is_favorite) return false;
      if (category && project.category !== category) return false;
      if (!term) return true;
      return [project.name, project.url, project.category, project.description]
        .some((field) => field.toLowerCase().includes(term));
    });
  }, [projects, view, category, search]);

  const categories = useMemo(
    () => Array.from(new Set(projects.map((project) => project.category).filter(Boolean))),
    [projects],
  );

  const stats = useMemo(() => ({
    total: projects.length,
    enabled: projects.filter((project) => project.is_enabled).length,
    favorites: projects.filter((project) => project.is_favorite).length,
  }), [projects]);

  // 只给当前页真正会渲染的卡片抓截图，切页时释放上一批 blob。
  const screenshotIds = useMemo(() => {
    if (view === "settings") return "";
    const source = view === "workbench" ? projects : visibleProjects;
    return source.filter((project) => project.has_screenshot).map((project) => project.id).join(",");
  }, [view, projects, visibleProjects]);

  useEffect(() => {
    let cancelled = false;
    Object.values(screenshotUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
    screenshotUrlsRef.current = {};
    setScreenshotUrls({});

    const ids = screenshotIds ? screenshotIds.split(",") : [];
    if (!ids.length) return;

    void Promise.all(ids.map(async (id) => {
      try {
        const blob = await getProjectScreenshot(id, session.accessToken);
        return [id, URL.createObjectURL(blob)] as const;
      } catch {
        return null;
      }
    })).then((entries) => {
      const next = Object.fromEntries(entries.filter((entry): entry is readonly [string, string] => Boolean(entry)));
      if (cancelled) {
        Object.values(next).forEach((url) => URL.revokeObjectURL(url));
        return;
      }
      screenshotUrlsRef.current = next;
      setScreenshotUrls(next);
    });

    return () => {
      cancelled = true;
      Object.values(screenshotUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
      screenshotUrlsRef.current = {};
    };
  }, [screenshotIds, session.accessToken]);

  const openCreate = () => { setEditingProject(null); setDrawerOpen(true); };
  const openEdit = (project: WebProject) => { setEditingProject(project); setDrawerOpen(true); };

  async function handleSave(payload: ProjectPayload) {
    if (editingProject) await updateProject(editingProject.id, payload, session.accessToken);
    else await createProject(payload, session.accessToken);
    setDrawerOpen(false); setNotice("系统已保存"); await refresh();
  }

  async function handleReveal(project: WebProject) {
    try {
      const result = await revealProjectCredential(project.id, session.accessToken);
      if (!result.password) { setError("该系统未配置密码"); return; }
      if (await copyText(result.password)) setNotice("密码已复制"); else setError("当前浏览器不支持自动复制");
    } catch (copyError) {
      setError(copyError instanceof Error ? copyError.message : "密码复制失败");
    }
  }

  async function handleFavorite(project: WebProject) {
    try {
      await updateProject(project.id, { is_favorite: !project.is_favorite }, session.accessToken);
      await refresh();
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "更新失败");
    }
  }

  async function handleDelete(project: WebProject) {
    if (!window.confirm(`确定删除“${project.name}”吗？删除后无法恢复。`)) return;
    try {
      await deleteProject(project.id, session.accessToken);
      setNotice("系统已删除");
      await refresh();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "删除失败");
    }
  }

  function handleNavigate(nextView: WorkspaceView) {
    setView(nextView);
    setError("");
    if (nextView !== "settings") setSearch("");
    if (nextView === "workbench") setCategory("");
  }

  function handleSaveDisplayName(value: string) {
    saveDisplayName(value);
    setDisplayName(value);
    setNotice("显示名称已保存");
  }

  const shownName = displayName || session.user.username;
  const cardHandlers = {
    onCopy: (project: WebProject) => void handleReveal(project),
    onFavorite: (project: WebProject) => void handleFavorite(project),
    onEdit: openEdit,
    onDelete: (project: WebProject) => void handleDelete(project),
  };

  return (
    <AppShell
      activeView={view}
      onNavigate={handleNavigate}
      displayName={shownName}
      username={session.user.username}
      onLogout={onLogout}
    >
      {view === "workbench" && (
        <WorkbenchPage
          projects={projects}
          stats={stats}
          focusId={focusId}
          onFocusChange={setFocusId}
          screenshotUrls={screenshotUrls}
          isLoading={isLoading}
          error={error}
          onDismissError={() => setError("")}
          onShowAll={() => handleNavigate("projects")}
          onCreate={openCreate}
          {...cardHandlers}
        />
      )}

      {(view === "projects" || view === "favorites") && (
        <ProjectsPage
          mode={view === "favorites" ? "favorites" : "all"}
          stats={stats}
          projects={visibleProjects}
          categories={categories}
          search={search}
          onSearchChange={setSearch}
          category={category}
          onCategoryChange={setCategory}
          layout={layout}
          onLayoutChange={setLayout}
          screenshotUrls={screenshotUrls}
          isLoading={isLoading}
          error={error}
          onDismissError={() => setError("")}
          onCreate={openCreate}
          {...cardHandlers}
        />
      )}

      {view === "settings" && (
        <SettingsPage
          displayName={shownName}
          username={session.user.username}
          onSaveDisplayName={handleSaveDisplayName}
          onLogout={onLogout}
        />
      )}

      <Toast message={notice} onDismiss={() => setNotice("")} />
      <ProjectDrawer
        open={drawerOpen}
        project={editingProject}
        onClose={() => setDrawerOpen(false)}
        onSave={handleSave}
      />
    </AppShell>
  );
}
