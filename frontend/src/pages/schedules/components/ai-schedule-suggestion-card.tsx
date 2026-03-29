import type { ActionModuleType } from '../api/types';
import {
  Cancel01Icon,
  GridViewIcon,
  MagicWand01Icon,
  Time02Icon,
} from '@hugeicons/core-free-icons';
import Icon from '~/components/common/icon';
import { cn } from '~/lib/utils';

export interface AiScheduleSuggestionData {
  time: string;
  actionModuleType: ActionModuleType;
  roomId: number;
  pattern: string;
  reason: string;
}

interface AiScheduleSuggestionCardProps {
  suggestion: AiScheduleSuggestionData;
  onClick: (data: AiScheduleSuggestionData) => void;
  onDismiss: () => void;
  className?: string;
}

export default function AiScheduleSuggestionCard({
  suggestion,
  onClick,
  onDismiss,
  className,
}: AiScheduleSuggestionCardProps) {
  // roomId를 활용한 방 이름 선언
  const roomName = `${suggestion.roomId}번 방`;

  const deviceName
    = suggestion.actionModuleType === 'AIR_PURIFIER' ? '공기청정기' : '가습기';

  return (
    <div className={cn('relative w-full', className)}>
      <button
        type="button"
        onClick={() => {
          onClick(suggestion);
        }}
        className="group relative flex w-full flex-col gap-3 overflow-hidden rounded-2xl border border-brand/10 bg-gradient-to-br from-brand-subtle/50 via-white to-white p-4 text-left shadow-sm transition-all hover:shadow-lg hover:shadow-brand/5 active:scale-[0.98]"
      >
        <div className="absolute -right-4 -top-4 text-brand/5 transition-transform group-hover:rotate-12 group-hover:scale-110">
          <Icon icon={MagicWand01Icon} size="md" color="currentColor" />
        </div>

        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand text-white shadow-sm shadow-brand/20">
              <Icon icon={MagicWand01Icon} size="xs" color="currentColor" />
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] font-bold uppercase tracking-widest text-brand/70">
                {roomName}
                {' '}
                AI 분석
              </span>
              <span className="text-xs font-extrabold text-fg-strong">
                {suggestion.pattern}
              </span>
            </div>
          </div>
          <div className="mr-6 shrink-0 rounded-full bg-white px-2.5 py-0.5 text-[10px] font-bold text-brand shadow-sm border border-brand/5">
            추천
          </div>
        </div>

        <div className="flex flex-col gap-1 mt-0.5">
          <div className="flex items-center gap-1 text-fg-muted">
            <Icon icon={GridViewIcon} size="xs" color="currentColor" />
            <span className="text-[11px] font-medium">
              {deviceName}
              {' '}
              가동 추천
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xl font-black tracking-tight text-fg-strong leading-tight">
            <Icon icon={Time02Icon} size="sm" color="brand" />
            <span>
              매일
              {' '}
              <span className="text-brand underline underline-offset-2 decoration-brand/30">
                {suggestion.time}
              </span>
              {' '}
              시작
            </span>
          </div>
        </div>

        <div className="rounded-xl bg-brand/5 p-3 text-xs leading-relaxed text-fg-default border border-brand/5 relative mt-1">
          <p className="line-clamp-2 font-medium opacity-90">
            {suggestion.reason}
          </p>
        </div>
      </button>

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onDismiss();
        }}
        className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-surface-sunken/80 text-fg-muted backdrop-blur-sm transition-colors hover:bg-surface-sunken hover:text-fg-strong z-10"
      >
        <Icon icon={Cancel01Icon} size="xs" color="currentColor" />
      </button>
    </div>
  );
}
