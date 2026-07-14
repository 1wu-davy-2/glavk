import { ExternalLink, LayoutGrid, LogOut, Settings, Star } from "lucide-react";
import type { ReactNode } from "react";

interface AppShellProps {
  username: string;
  favoriteOnly: boolean;
  onShowAll: () => void;
  onShowFavorites: () => void;
  onLogout: () => void;
  children: ReactNode;
}

export function AppShell({ username, favoriteOnly, onShowAll, onShowFavorites, onLogout, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand"><span className="brand-mark"><LayoutGrid size={19} /></span><span className="brand-copy"><strong>glavk</strong><small>网页系统管理</small></span></div>
          <span className="sidebar-kicker">工作台</span>
          <nav className="route-nav" aria-label="主导航">
            <button className={`route-link ${!favoriteOnly ? "is-active" : ""}`} type="button" onClick={onShowAll}><LayoutGrid size={16} /> 网页系统</button>
            <button className={`route-link ${favoriteOnly ? "is-active" : ""}`} type="button" onClick={onShowFavorites}><Star size={16} /> 收藏项目</button>
            <button className="route-link route-link-muted" type="button" disabled><Settings size={16} /> 设置</button>
          </nav>
        </div>
        <div className="sidebar-bottom"><div className="profile-card"><span className="profile-avatar">{username.slice(0, 1).toUpperCase()}</span><span><strong>{username}</strong><small>管理员</small></span></div><button className="logout-link" type="button" onClick={onLogout}><LogOut size={15} /> 退出登录</button></div>
      </aside>
      <main className="main-area"><header className="topbar"><div className="breadcrumb"><span>工作台</span><strong>/</strong><b>网页系统</b></div><a className="topbar-help" href="https://stitch.withgoogle.com/projects/10559855834040172715" target="_blank" rel="noreferrer"><ExternalLink size={14} /> 设计参考</a></header>{children}</main>
    </div>
  );
}

