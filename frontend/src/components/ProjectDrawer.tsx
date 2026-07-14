import { useEffect, useState, type FormEvent } from "react";
import { Check, Eye, EyeOff, X } from "lucide-react";

import type { ProjectPayload, WebProject } from "../types";

const emptyForm: ProjectPayload = { name: "", url: "", category: "未分类", description: "", notes: "", username: "", password: "", is_favorite: false, is_enabled: true, sort_order: 0 };

interface ProjectDrawerProps { open: boolean; project: WebProject | null; onClose: () => void; onSave: (payload: ProjectPayload) => Promise<void>; }

export function ProjectDrawer({ open, project, onClose, onSave }: ProjectDrawerProps) {
  const [form, setForm] = useState<ProjectPayload>(emptyForm);
  const [showPassword, setShowPassword] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { setShowPassword(false); setError(""); setForm(project ? { name: project.name, url: project.url, category: project.category, description: project.description, notes: project.notes, username: project.username, password: "", is_favorite: project.is_favorite, is_enabled: project.is_enabled, sort_order: project.sort_order } : emptyForm); }, [project, open]);
  if (!open) return null;
  const update = <K extends keyof ProjectPayload>(key: K, value: ProjectPayload[K]) => setForm((current) => ({ ...current, [key]: value }));

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.name.trim() || !form.url.trim()) { setError("请填写系统名称和访问地址"); return; }
    setError(""); setIsSaving(true);
    try { await onSave({ ...form, password: form.password?.trim() || undefined }); } catch (saveError) { setError(saveError instanceof Error ? saveError.message : "保存失败，请稍后重试"); } finally { setIsSaving(false); }
  }

  return <div className="drawer-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><aside className="project-drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title"><header className="drawer-header"><div><span className="eyebrow">系统资料</span><h2 id="drawer-title">{project ? "编辑网页系统" : "添加网页系统"}</h2></div><button className="icon-button" type="button" aria-label="关闭抽屉" title="关闭抽屉" onClick={onClose}><X size={18} /></button></header><form className="drawer-form" onSubmit={submit}><label>系统名称<input aria-label="系统名称" value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="例如：客户管理后台" /></label><label>访问地址<input aria-label="访问地址" type="url" value={form.url} onChange={(event) => update("url", event.target.value)} placeholder="https://example.com" /></label><label>系统分类<input aria-label="系统分类" value={form.category} onChange={(event) => update("category", event.target.value)} placeholder="业务系统" /></label><label>登录用户名<input aria-label="登录用户名" value={form.username} onChange={(event) => update("username", event.target.value)} placeholder="管理员账号" /></label><label>系统密码<span className="password-input"><input aria-label="系统密码" type={showPassword ? "text" : "password"} value={form.password ?? ""} onChange={(event) => update("password", event.target.value)} placeholder={project ? "留空表示不修改" : "登录密码"} /><button className="icon-button" type="button" aria-label={showPassword ? "隐藏系统密码" : "显示系统密码"} title={showPassword ? "隐藏系统密码" : "显示系统密码"} onClick={() => setShowPassword((value) => !value)}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button></span></label><label>项目简介<textarea aria-label="项目简介" value={form.description} onChange={(event) => update("description", event.target.value)} rows={2} placeholder="一句话说明用途" /></label><label>备注<textarea aria-label="备注" value={form.notes} onChange={(event) => update("notes", event.target.value)} rows={3} placeholder="补充使用说明" /></label><div className="toggle-row"><label className="checkbox-label"><input type="checkbox" checked={form.is_favorite} onChange={(event) => update("is_favorite", event.target.checked)} /> 收藏项目</label><label className="checkbox-label"><input type="checkbox" checked={form.is_enabled} onChange={(event) => update("is_enabled", event.target.checked)} /> 启用系统</label></div>{error && <p className="form-error" role="alert">{error}</p>}<footer className="drawer-footer"><button className="button button-secondary" type="button" onClick={onClose}>取消</button><button className="button button-primary" type="submit" disabled={isSaving}>{isSaving ? "保存中..." : <><Check size={15} /> 保存系统</>}</button></footer></form></aside></div>;
}
