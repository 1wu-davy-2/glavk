import { CheckCircle2, X } from "lucide-react";

export function Toast({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  if (!message) return null;
  return <div className="toast" role="status"><CheckCircle2 size={17} /><span>{message}</span><button type="button" className="icon-button" aria-label="关闭提示" title="关闭提示" onClick={onDismiss}><X size={15} /></button></div>;
}

