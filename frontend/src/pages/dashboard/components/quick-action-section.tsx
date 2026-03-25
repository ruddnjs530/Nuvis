import AppCard from '~/components/common/app-card';
import SectionHeader from '~/components/common/section-header';
import { cn } from '~/lib/utils';

// ── Mock data ────────────────────────────────────────────────────────────────
// Phase 3: useQuery로 서버 목록 교체
const QUICK_ACTIONS = [
  { id: 'station', label: '스테이션 복귀' },
] as const;

// ── Section ───────────────────────────────────────────────────────────────────
export default function QuickActionSection() {
  function handleAction(id: string) {
    // Phase 3: useMutation → 로봇 명령 API
    console.warn('[QuickAction]', id);
  }

  return (
    <section>
      <SectionHeader>빠른 동작</SectionHeader>

      <div className="px-4">
        <AppCard className="px-4">
          {QUICK_ACTIONS.map((action, idx) => (
            <div
              key={action.id}
              className={cn(
                'flex items-center px-2',
                idx < QUICK_ACTIONS.length - 1 && 'border-b border-border-default',
              )}
            >
              <button
                type="button"
                onClick={() => handleAction(action.id)}
                className="flex-1 py-6 text-left text-sm text-fg-muted transition-colors hover:text-primary"
              >
                {action.label}
              </button>
            </div>
          ))}
        </AppCard>

        {/* <SectionLinkFooter to="/quick-actions/edit">등록 / 수정하기</SectionLinkFooter> */}
      </div>
    </section>
  );
}
