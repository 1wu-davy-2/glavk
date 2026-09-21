import { Home, KeyRound, LayoutGrid, LogOut, Settings, Star } from "lucide-react";
import type { ReactNode } from "react";

import type { WorkspaceView } from "../types";

const NAV_ITEMS: Array<{ view: WorkspaceView; label: string; icon: typeof Home }> = [
  { view: "workbench", label: "工作台", icon: Home },
  { view: "projects", label: "网页系统", icon: LayoutGrid },
  { view: "favorites", label: "收藏项目", icon: Star },
  { view: "settings", label: "设置", icon: Settings },
];

interface AppShellProps {
  activeView: WorkspaceView;
  onNavigate: (view: WorkspaceView) => void;
  displayName: string;
  username: string;
  onLogout: () => void;
  children: ReactNode;
}

export function AppShell({ activeView, onNavigate, displayName, username, onLogout, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><KeyRound size={19} /></span>
          <span className="brand-copy"><strong>glavk</strong><small>网页系统管理</small></span>
        </div>

        <span className="sidebar-kicker">工作区</span>
        <nav className="route-nav" aria-label="主导航">
          {NAV_ITEMS.map(({ view, label, icon: Icon }) => (
            <button
              key={view}
              className={`route-link ${activeView === view ? "is-active" : ""}`}
              type="button"
              aria-current={activeView === view ? "page" : undefined}
              onClick={() => onNavigate(view)}
            >
              <Icon size={17} /> {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="profile-card">
            <span className="profile-avatar">{displayName.slice(0, 1).toUpperCase()}</span>
            <span className="profile-copy">
              <strong>{displayName}</strong>
              <small>{displayName === username ? "本地管理员" : username}</small>
            </span>
            <button className="logout-link" type="button" aria-label="退出登录" title="退出登录" onClick={onLogout}>
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>
      <main className="main-area">{children}</main>
    </div>
  );
}
