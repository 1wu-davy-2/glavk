import { useState, type FormEvent } from "react";
import { ArrowRight, Eye, EyeOff, KeyRound, ShieldCheck } from "lucide-react";

import type { AuthSession } from "../types";

interface LoginPageProps {
  onLogin: (username: string, password: string) => Promise<AuthSession>;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await onLogin(username.trim(), password);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "登录失败，请稍后重试");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-panel" aria-labelledby="login-title">
        <div className="auth-brand-mark"><KeyRound size={22} /></div>
        <span className="eyebrow">网页系统管理</span>
        <h1 id="login-title">登录 glavk</h1>
        <p className="auth-intro">集中管理你的网页系统入口与登录凭据。</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            管理员账号
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
          </label>
          <label>
            登录密码
            <span className="password-input">
              <input type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
              <button type="button" className="icon-button" aria-label={showPassword ? "隐藏密码" : "显示密码"} title={showPassword ? "隐藏密码" : "显示密码"} onClick={() => setShowPassword((value) => !value)}>
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </span>
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "登录中..." : "登录"} <ArrowRight size={17} />
          </button>
        </form>
        <div className="auth-footnote"><span /><ShieldCheck size={14} /> 安全连接 · 管理员入口 <span /></div>
      </section>
    </main>
  );
}

