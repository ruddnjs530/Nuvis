import type { Schedule } from '../api/types';
import { Cancel01Icon, Edit01Icon, TimeManagementIcon } from '@hugeicons/core-free-icons';
import AppCard from '~/components/common/app-card';
import Icon from '~/components/common/icon';
import { Switch } from '~/components/ui/switch';

// ── 룸 이름 / 모듈 이름 매핑 ─────────────────────────────────────────────────
const ROOM_LABELS: Record<number, string> = {
  1: '거실',
  2: '침실',
  3: '부엌',
};

const MODULE_LABELS: Record<string, string> = {
  AIR_PURIFIER: '공기청정기',
  HUMIDIFIER: '가습기',
};

// ── 헬퍼: ISO 시간부 → "오전/오후 H:mm" (UTC 기준, 폼과 동일)
function formatTime(isoTime: string): string {
  const d = new Date(isoTime);
  const utcH = d.getUTCHours();
  const utcM = String(d.getUTCMinutes()).padStart(2, '0');
  const period = utcH >= 12 ? '오후' : '오전';
  const displayH = utcH % 12 === 0 ? 12 : utcH % 12;
  return `${period} ${displayH}:${utcM}`;
}

// ── Props ─────────────────────────────────────────────────────────────────────
interface ScheduleCardProps {
  schedule: Schedule;
  onToggle: (schedule: Schedule, active: boolean) => void;
  onEdit: (schedule: Schedule) => void;
  onDelete: (schedule: Schedule) => void;
}

export default function ScheduleCard({ schedule, onToggle, onEdit, onDelete }: ScheduleCardProps) {
  const roomLabel = ROOM_LABELS[schedule.roomId] ?? '알 수 없는 방';
  const moduleLabel = MODULE_LABELS[schedule.actionModuleType] ?? schedule.actionModuleType;
  const powerLabel = schedule.actionModulePower ? '켜기' : '끄기';
  const badgeText = `${roomLabel} • ${moduleLabel} ${powerLabel} (Lv.${schedule.actionModuleLevel})`;

  return (
    <AppCard className="flex flex-col gap-4 p-5">
      {/* 상단: 시간 + 스위치 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* 시간 아이콘 */}
          <div className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-full bg-brand-subtle text-brand">
            <Icon icon={TimeManagementIcon} size="md" color="brand" strokeWidth={2} />
          </div>
          {/* 시간 + 가동 시간 */}
          <div className="flex flex-col">
            <span className="text-2xl font-bold tabular-nums text-fg-strong leading-tight">
              {formatTime(schedule.startTime)}
            </span>
            <span className="text-xs text-fg-muted">
              {schedule.durationMinutes}
              분 가동
            </span>
          </div>
        </div>

        <Switch
          checked={schedule.isActive}
          onCheckedChange={checked => onToggle(schedule, checked)}
        />
      </div>

      {/* 중단: 액션 뱃지 */}
      <div className="flex items-center gap-3 rounded-lg bg-surface-sunken px-4 py-3">
        <span className="text-sm text-fg-default">{badgeText}</span>
      </div>

      {/* 하단: 수정 · 삭제 */}
      <div className="flex items-center justify-end gap-5 pt-1">
        <button
          type="button"
          onClick={() => onEdit(schedule)}
          className="flex items-center gap-1.5 text-sm text-fg-default transition-colors hover:text-fg-strong"
        >
          <Icon icon={Edit01Icon} size="xs" color="currentColor" strokeWidth={2} />
          <span>수정</span>
        </button>
        <button
          type="button"
          onClick={() => onDelete(schedule)}
          className="flex items-center gap-1.5 text-sm text-fg-default transition-colors hover:text-red-500"
        >
          <Icon icon={Cancel01Icon} size="xs" color="currentColor" strokeWidth={2} />
          <span>삭제</span>
        </button>
      </div>
    </AppCard>
  );
}
