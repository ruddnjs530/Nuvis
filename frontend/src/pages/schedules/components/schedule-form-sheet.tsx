import type { ActionModuleType, CreateScheduleRequest, Schedule } from '../api/types';
import { MinusSignIcon, PlusSignIcon } from '@hugeicons/core-free-icons';
import { useState } from 'react';
import Icon from '~/components/common/icon';
import { Button } from '~/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '~/components/ui/sheet';
import { cn } from '~/lib/utils';

// ── Options ──────────────────────────────────────────────────────────────────
const ROOM_OPTIONS = [
  { id: 2, label: '거실' },
  { id: 5, label: '침실' },
  { id: 4, label: '부엌' },
];

const MODULE_OPTIONS = [
  { id: 'AIR_PURIFIER', label: '공기청정기' },
  { id: 'HUMIDIFIER', label: '가습기' },
];

function Chip({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-full border px-4 py-2 text-sm font-medium transition-colors',
        active
          ? 'border-brand bg-brand text-white'
          : 'border-border-default bg-surface text-fg-muted hover:bg-surface-sunken',
      )}
    >
      {label}
    </button>
  );
}

function timeToIso(hhmm: string): string {
  return `1970-01-01T${hhmm}:00.000Z`;
}

function isoToTime(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getUTCHours()).padStart(2, '0');
  const mm = String(d.getUTCMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

export interface ScheduleFormData {
  time: string;
  durationMinutes: number;
  roomId: number;
  actionModuleType: ActionModuleType;
}

interface ScheduleFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schedule: Schedule | null;
  initialData?: Partial<ScheduleFormData> | null; // AI 데이터 주입용 추가
  onSave: (data: CreateScheduleRequest) => void;
}

function getInitialForm(schedule: Schedule | null, initialData?: Partial<ScheduleFormData> | null): ScheduleFormData {
  if (schedule) {
    return {
      time: isoToTime(schedule.startTime),
      durationMinutes: schedule.durationMinutes,
      roomId: schedule.roomId,
      actionModuleType: schedule.actionModuleType,
    };
  }
  return {
    time: initialData?.time ?? '08:00',
    durationMinutes: initialData?.durationMinutes ?? 60,
    roomId: initialData?.roomId ?? 1,
    actionModuleType: initialData?.actionModuleType ?? 'AIR_PURIFIER',
  };
}

export default function ScheduleFormSheet({ open, onOpenChange, schedule, initialData, onSave }: ScheduleFormSheetProps) {
  const isEditMode = schedule !== null;
  const [form, setForm] = useState<ScheduleFormData>(() => getInitialForm(schedule, initialData));

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
  };

  const adjustDuration = (delta: number) =>
    setForm(prev => ({ ...prev, durationMinutes: Math.max(15, prev.durationMinutes + delta) }));

  const handleSave = () => {
    onSave({
      startTime: timeToIso(form.time),
      durationMinutes: form.durationMinutes,
      roomId: form.roomId,
      actionModuleType: form.actionModuleType,
      isActive: isEditMode ? (schedule?.isActive ?? true) : true,
    });
  };

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="bottom" className="max-h-[90dvh] overflow-y-auto rounded-t-3xl px-6 pb-10 pt-6">
        <SheetHeader className="mb-6 flex flex-row items-center justify-between">
          <SheetTitle className="text-xl font-bold text-fg-strong">
            {isEditMode ? '스케줄 수정' : initialData ? 'AI 추천 스케줄 등록' : '새 스케줄'}
          </SheetTitle>
        </SheetHeader>

        <div className="flex flex-col gap-7">
          <div className="flex flex-col gap-2">
            <label className="pl-1 text-sm font-bold text-fg-strong">가동 시작 시간</label>
            <input
              type="time"
              value={form.time}
              onChange={e => setForm(prev => ({ ...prev, time: e.target.value }))}
              className="w-full rounded-xl border border-border-default bg-surface px-4 py-3 text-2xl font-bold tabular-nums text-fg-strong outline-none transition-colors focus:border-brand focus:ring-1 focus:ring-brand"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="pl-1 text-sm font-bold text-fg-strong">가동 시간 (분)</label>
            <div className="flex items-center justify-between rounded-xl border border-border-default bg-surface px-4 py-3">
              <button
                type="button"
                onClick={() => adjustDuration(-10)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-sunken transition-colors hover:bg-border-default"
              >
                <Icon icon={MinusSignIcon} size="sm" color="currentColor" />
              </button>
              <span className="text-2xl font-bold tabular-nums text-fg-strong">
                {form.durationMinutes}
                분
              </span>
              <button
                type="button"
                onClick={() => adjustDuration(10)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-sunken transition-colors hover:bg-border-default"
              >
                <Icon icon={PlusSignIcon} size="sm" color="currentColor" />
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="pl-1 text-sm font-bold text-fg-strong">방</label>
            <div className="flex flex-wrap gap-2">
              {ROOM_OPTIONS.map(r => (
                <Chip key={r.id} label={r.label} active={form.roomId === r.id} onClick={() => setForm(prev => ({ ...prev, roomId: r.id }))} />
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="pl-1 text-sm font-bold text-fg-strong">모듈</label>
            <div className="flex flex-wrap gap-2">
              {MODULE_OPTIONS.map(m => (
                <Chip key={m.id} label={m.label} active={form.actionModuleType === m.id} onClick={() => setForm(prev => ({ ...prev, actionModuleType: m.id as ActionModuleType }))} />
              ))}
            </div>
          </div>

          <Button variant="brand" size="xl" className="mt-2 w-full" onClick={handleSave}>
            저장하기
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
