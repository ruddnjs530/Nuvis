import type { Toast } from '~/store/toast-store';
import { Alert01Icon } from '@hugeicons/core-free-icons';
import Icon from '~/components/common/icon';
import { useToastStore } from '~/store/toast-store';

const TYPE_STYLES: Record<Toast['type'], { bg: string; border: string; icon: string }> = {
  info: { bg: 'rgba(19,127,236,0.10)', border: 'rgba(19,127,236,0.30)', icon: '#137FEC' },
  success: { bg: 'rgba(16,185,129,0.10)', border: 'rgba(16,185,129,0.30)', icon: '#10B981' },
  warning: { bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.30)', icon: '#F59E0B' },
  error: { bg: 'rgba(239,68,68,0.10)', border: 'rgba(239,68,68,0.30)', icon: '#EF4444' },
};

function ToastItem({ toast }: { toast: Toast }) {
  const remove = useToastStore(s => s.remove);
  const s = TYPE_STYLES[toast.type];

  return (
    <div
      role="alert"
      aria-live="assertive"
      onClick={() => remove(toast.id)}
      className="animate-in fade-in slide-in-from-top-2 duration-300 flex w-full cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 shadow-lg backdrop-blur-lg"
      style={{ background: s.bg, borderColor: s.border, color: s.icon }}
    >
      <Icon icon={Alert01Icon} size="md" className="mt-0.5 shrink-0" />
      <p className="text-sm leading-relaxed" style={{ color: '#0F172A' }}>
        {toast.message}
      </p>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useToastStore(s => s.toasts);

  return (
    <div
      aria-label="알림"
      className="pointer-events-none fixed top-20 left-1/2 z-9999 flex w-full max-w-md -translate-x-1/2 flex-col gap-2 px-4"
    >
      {toasts.map(t => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem toast={t} />
        </div>
      ))}
    </div>
  );
}
