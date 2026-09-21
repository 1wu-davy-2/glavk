import { LayoutGrid, List, Plus, Search, TriangleAlert } from "lucide-react";

import type { ProjectLayout, WebProject } from "../types";
import { PageHeader } from "./PageHeader";
import { ProjectCard } from "./ProjectCard";
import { StatBar } from "./StatBar";

export interface ProjectStats {
  total: number;
  enabled: number;
  favorites: number;
}

interface ProjectsPageProps {
  mode: "all" | "favorites";
  stats: ProjectStats;
  projects: WebProject[];
  categories: string[];
  search: string;
  onSearchChange: (value: string) => void;
  category: string;
  onCategoryChange: (value: string) => void;
  layout: ProjectLayout;
  onLayoutChange: (value: ProjectLayout) => void;
  screenshotUrls: Record<string, string>;
  isLoading: boolean;
  error: string;
  onDismissError: () => void;
  onCreate: () => void;
  onCopy: (project: WebProject) => void;
  onFavorite: (project: WebProject) => void;
  onEdit: (project: WebProject) => void;
  onDelete: (project: WebProject) => void;
}

export function ProjectsPage({
  mode, stats, projects, categories, search, onSearchChange, category, onCategoryChange,
  layout, onLayoutChange, screenshotUrls, isLoading, error, onDismissError, onCreate,
  onCopy, onFavorite, onEdit, onDelete,
}: ProjectsPageProps) {
  const favoritesOnly = mode === "favorites";
  const isFiltered = Boolean(search.trim()) || Boolean(category) || favoritesOnly;

  return (
    <div className="workspace-page">
      <PageHeader
        eyebrow="管理中心"
        title={favoritesOnly ? "收藏项目" : "网页系统"}
        description={favoritesOnly ? "常用入口单独列出，星标随时可以取消。" : "所有业务入口与登录凭证，集中在这个目录里。"}
        action={<button className="button button-primary" type="button" onClick={onCreate}><Plus size={16} /> 添加系统</button>}
      />

      <StatBar total={stats.total} enabled={stats.enabled} favorites={stats.favorites} />

      <section className="project-section">
        <div className="section-toolbar">
          <div>
            <span className="eyebrow">系统目录</span>
            <h2>{favoritesOnly ? "收藏项目" : "全部项目"}<span>{projects.length.toString().padStart(2, "0")}</span></h2>
          </div>
          <div className="filter-tools">
            <label className="search-field">
              <Search size={16} />
              <span className="sr-only">搜索系统名称或地址</span>
              <input
                aria-label="搜索系统名称或地址"
                placeholder="搜索名称或地址"
                value={search}
                onChange={(event) => onSearchChange(event.target.value)}
              />
            </label>
            <div className="layout-toggle" role="group" aria-label="切换视图">
              <button
                className={`layout-button ${layout === "grid" ? "is-active" : ""}`}
                type="button"
                aria-label="网格视图"
                aria-pressed={layout === "grid"}
                onClick={() => onLayoutChange("grid")}
              >
                <LayoutGrid size={16} />
              </button>
              <button
                className={`layout-button ${layout === "list" ? "is-active" : ""}`}
                type="button"
                aria-label="列表视图"
                aria-pressed={layout === "list"}
                onClick={() => onLayoutChange("list")}
              >
                <List size={16} />
              </button>
            </div>
          </div>
        </div>

        <div className="category-chips">
          <button
            className={`chip ${category === "" ? "is-active" : ""}`}
            type="button"
            onClick={() => onCategoryChange("")}
          >
            全部分类
          </button>
          {categories.map((item) => (
            <button
              key={item}
              className={`chip ${category === item ? "is-active" : ""}`}
              type="button"
              onClick={() => onCategoryChange(item)}
            >
              {item}
            </button>
          ))}
        </div>

        {error && (
          <div className="inline-error" role="alert">
            <TriangleAlert size={16} /> {error}
            <button className="icon-button" type="button" aria-label="关闭错误" onClick={onDismissError}>×</button>
          </div>
        )}

        {isLoading ? (
          <div className="project-grid">
            {[1, 2, 3].map((item) => <div className="project-skeleton" key={item}><span /><span /><span /><span /></div>)}
          </div>
        ) : projects.length ? (
          <div className={`project-grid ${layout === "list" ? "is-list" : ""}`}>
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                screenshotUrl={screenshotUrls[project.id]}
                onCopy={() => onCopy(project)}
                onFavorite={() => onFavorite(project)}
                onEdit={() => onEdit(project)}
                onDelete={() => onDelete(project)}
              />
            ))}
          </div>
        ) : (
          <div className="empty-panel">
            <span className="empty-icon"><LayoutGrid size={22} /></span>
            <span className="eyebrow">系统目录为空</span>
            <h3>{isFiltered ? "没有匹配的系统" : "还没有网页系统"}</h3>
            <p>{isFiltered ? "调整搜索或筛选条件后再试一次" : "添加你的第一个网页系统，开始建立统一入口"}</p>
            {!isFiltered && (
              <button className="button button-primary" type="button" onClick={onCreate}>
                <Plus size={16} /> 添加第一个系统
              </button>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
