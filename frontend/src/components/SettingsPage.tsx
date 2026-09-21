import { useState } from "react";
import { LogOut } from "lucide-react";

import { PageHeader } from "./PageHeader";

interface SettingsPageProps {
  displayName: string;
  username: string;
  onSaveDisplayName: (value: string) => void;
  onLogout: () => void;
}

export function SettingsPage({ displayName, username, onSaveDisplayName, onLogout }: SettingsPageProps) {
  const [draft, setDraft] = useState(displayName);

  return (
    <div className="workspace-page workspace-page-narrow">
      <PageHeader
        eyebrow="管理中心"
        title="设置"
        description="显示名称只留在这台设备，系统数据保存在服务端。"
      />

      <section className="settings-card">
        <header>
          <h2>个人资料</h2>
          <p>出现在侧栏底部的称呼。</p>
        </header>
        <label className="settings-field">
          显示名称
          <input
            aria-label="显示名称"
            value={draft}
            maxLength={24}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={username}
          />
        </label>
        <button className="button button-primary button-small" type="button" onClick={() => onSaveDisplayName(draft.trim())}>
          保存
        </button>
      </section>

      <section className="settings-card">
        <header>
          <h2>数据存放</h2>
          <p>系统地址、用户名和密码由后端加密保存在你自己的服务器上，登录凭据只在复制密码时于浏览器内存中解密。</p>
        </header>
        <p className="settings-note">
          当前登录账号：<strong>{username}</strong>。清除浏览器数据只会让你退出登录，不会删除任何系统。
        </p>
        <button className="button button-ghost button-small" type="button" onClick={onLogout}>
          <LogOut size={15} /> 退出登录
        </button>
      </section>

      <section className="settings-card">
        <header>
          <h2>关于 glavk</h2>
        </header>
        <p className="settings-note">
          这是一份给自己用的入口目录：少一层书签栏，多一处能放下凭证的抽屉。不是云端密码库，也没有第三方账号，数据只存在你自己的服务器上。
        </p>
      </section>
    </div>
  );
}
