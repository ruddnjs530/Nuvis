import type { Schedule } from '../api/types';
import { Cancel01Icon, Edit01Icon, PauseIcon, PlayIcon, Time02Icon } from '@hugeicons/core-free-icons';
import { useEffect, useState } from 'react';
import Icon from '~/components/common/icon';
import { cn } from '~/lib/utils';

// ── 상수 ──────────────────────────────────────────────────────────────────────
const PIXELS_PER_HOUR = 64;
const TOTAL_HEIGHT = PIXELS_PER_HOUR * 24;
const MIN_BLOCK_HEIGHT = 28;
const ALL_HOURS = Array.from({ length: 25 }, (_, i) => i);
const LABEL_HOURS = Array.from({ length: 13 }, (_, i) => i * 2);

// ── 레이블 매핑 ───────────────────────────────────────────────────────────────
const MODULE_LABELS: Record<string, string> = {
  AIR_PURIFIER: '공기청정기',
  HUMIDIFIER: '가습기',
};

const ROOM_LABELS: Record<number, string> = {
  1: '거실',
  2: '침실',
  3: '부엌',
};

// ── 시간 헬퍼 ────────────────────────────────────────────────────────────────
function getUtcMinutes(iso: string): number {
  const d = new Date(iso);
  return d.getUTCHours() * 60 + d.getUTCMinutes();
}

function formatUtcTime(iso: string): string {
  const d = new Date(iso);
  const h = d.getUTCHours();
  const m = String(d.getUTCMinutes()).padStart(2, '0');
  const period = h >= 12 ? '오후' : '오전';
  const displayH = h % 12 === 0 ? 12 : h % 12;
  return `${period} ${displayH}:${m}`;
}

function nowLocalMinutes(): number {
  const n = new Date();
  return n.getHours() * 60 + n.getMinutes();
}

// ── "현재 시각" 인디케이터 ─────────────────────────────────────────────────
function NowIndicator({ minutes }: { minutes: number }) {
  const top = (minutes / 60) * PIXELS_PER_HOUR;
  return (
    <div
      className="pointer-events-none absolute left-0 right-0 z-20 flex items-center"
      style={{ top, transform: 'translateY(-50%)' }}
    >
      {/* 맥박 점 */}
      <span className="relative flex h-2 w-2 shrink-0">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-60" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500 ring-2 ring-white" />
      </span>
      {/* 라인 */}
      <div className="h-[1.5px] flex-1 bg-red-400/70" />
    </div>
  );
}

// ── BlockSegment ──────────────────────────────────────────────────────────────
interface BlockSegmentProps {
  schedule: Schedule;
  top: number;
  height: number;
  isContinuation?: boolean;
  isTruncated?: boolean;
  isNowRunning?: boolean;
  onToggleActive: (s: Schedule) => void;
  onEdit: (s: Schedule) => void;
  onDelete: (s: Schedule) => void;
}

function BlockSegment({
  schedule,
  top,
  height,
  isContinuation = false,
  isTruncated = false,
  isNowRunning = false,
  onToggleActive,
  onEdit,
  onDelete,
}: BlockSegmentProps) {
  const isTall = height >= 58;
  const isActive = schedule.isActive;

  return (
    <div
      className={cn(
        'absolute inset-x-1 overflow-hidden transition-shadow',
        // rounding: accent bar side(left)는 항상 straight
        isContinuation
          ? 'rounded-br-lg rounded-tr-none rounded-bl-none rounded-tl-none'
          : isTruncated
            ? 'rounded-tr-lg rounded-br-none'
            : 'rounded-r-lg',
        isActive
          ? 'shadow-sm ring-1 ring-brand/20 z-0'
          : 'z-0',
        !isActive && 'opacity-55',
      )}
      style={{ top, height }}
    >
      {/* 왼쪽 컬러 액센트 바 */}
      <div
        className={cn(
          'absolute bottom-0 left-0 top-0 w-[4px]',
          isActive ? 'bg-brand' : 'bg-fg-subtle',
        )}
      />

      {/* 배경 색조 */}
      <div
        className={cn(
          'absolute inset-0',
          isActive ? 'bg-brand/8' : 'bg-surface-sunken/60',
        )}
      />

      {/* Shimmer Effect */}
      {isActive && isNowRunning && (
        <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[inherit]">
          <div className="absolute inset-0 w-[300%] animate-shimmer bg-gradient-to-r from-transparent via-white/50 to-transparent shadow-[0_0_15px_rgba(255,255,255,0.4)]" />
        </div>
      )}

      {/* 콘텐츠 */}
      <div className="relative flex h-full flex-col justify-between overflow-hidden py-2 pl-3 pr-2">
        {/* 헤더: 시각 + 가동시간 + 버튼 (main 블록만) */}
        {!isContinuation && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-2 overflow-hidden">
              <span
                className={cn(
                  'shrink-0 text-xs font-bold tabular-nums leading-none',
                  isActive ? 'text-brand' : 'text-fg-muted',
                )}
              >
                {formatUtcTime(schedule.startTime)}
              </span>
              <span className="flex shrink-0 items-center gap-0.5 text-[10px] leading-none text-fg-subtle">
                <Icon icon={Time02Icon} size="sm" color="currentColor" strokeWidth={1.5} />
                {schedule.durationMinutes}
                분
              </span>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(schedule);
                }}
                className="flex h-5 w-5 items-center justify-center rounded-full text-fg-subtle transition-colors hover:text-fg-strong"
                aria-label="수정"
              >
                <Icon icon={Edit01Icon} size="sm" color="currentColor" strokeWidth={2} />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleActive(schedule);
                }}
                className={cn(
                  'flex h-5 w-5 items-center justify-center rounded-full transition-colors',
                  isActive ? 'text-fg-subtle hover:text-fg-strong' : 'text-fg-subtle hover:text-brand',
                )}
                aria-label={isActive ? '일시정지' : '시작'}
              >
                <Icon icon={isActive ? PauseIcon : PlayIcon} size="sm" color="currentColor" strokeWidth={2} />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(schedule);
                }}
                className="flex h-5 w-5 items-center justify-center rounded-full text-fg-subtle transition-colors hover:text-red-500"
                aria-label="삭제"
              >
                <Icon icon={Cancel01Icon} size="xs" color="currentColor" strokeWidth={2} />
              </button>
            </div>
          </div>
        )}

        {/* 장소 · 모듈 요약 */}
        {isTall && (
          <span className="truncate text-[10px] leading-none text-fg-muted">
            {isContinuation ? '↑ ' : ''}
            {ROOM_LABELS[schedule.roomId] ?? '?'}
            {' '}
            •
            {' '}
            {MODULE_LABELS[schedule.actionModuleType] ?? schedule.actionModuleType}
          </span>
        )}
      </div>
    </div>
  );
}

// ── ScheduleBlock (자정 wrap 포함) ────────────────────────────────────────────
interface ScheduleBlockProps {
  schedule: Schedule;
  nowMin: number;
  onToggleActive: (s: Schedule) => void;
  onEdit: (s: Schedule) => void;
  onDelete: (s: Schedule) => void;
}

function ScheduleBlock({ schedule, nowMin, onToggleActive, onEdit, onDelete }: ScheduleBlockProps) {
  const TOTAL_MINUTES = 24 * 60;
  const startMin = getUtcMinutes(schedule.startTime);
  const endMin = startMin + schedule.durationMinutes;
  const overflowMin = endMin - TOTAL_MINUTES;

  const mainTop = (startMin / 60) * PIXELS_PER_HOUR;
  const mainH = Math.max(
    MIN_BLOCK_HEIGHT,
    Math.min(endMin - startMin, TOTAL_MINUTES - startMin) / 60 * PIXELS_PER_HOUR,
  );

  const isNowRunning = schedule.isActive && (
    (nowMin >= startMin && nowMin < endMin)
    || (overflowMin > 0 && nowMin < overflowMin)
  );

  return (
    <>
      <BlockSegment
        schedule={schedule}
        top={mainTop}
        height={mainH}
        isTruncated={overflowMin > 0}
        isNowRunning={isNowRunning && nowMin >= startMin}
        onToggleActive={onToggleActive}
        onEdit={onEdit}
        onDelete={onDelete}
      />
      {overflowMin > 0 && (
        <BlockSegment
          schedule={schedule}
          top={0}
          height={Math.max(MIN_BLOCK_HEIGHT, (overflowMin / 60) * PIXELS_PER_HOUR)}
          isContinuation
          isNowRunning={isNowRunning && nowMin < overflowMin}
          onToggleActive={onToggleActive}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      )}
    </>
  );
}

// ── ScheduleTimeline ──────────────────────────────────────────────────────────
interface ScheduleTimelineProps {
  schedules: Schedule[];
  onToggleActive: (s: Schedule) => void;
  onEdit: (s: Schedule) => void;
  onDelete: (s: Schedule) => void;
}

export default function ScheduleTimeline({
  schedules,
  onToggleActive,
  onEdit,
  onDelete,
}: ScheduleTimelineProps) {
  const [nowMin, setNowMin] = useState(() => nowLocalMinutes());

  // 매 분마다 현재 시각 업데이트
  useEffect(() => {
    const id = setInterval(() => {
      setNowMin(nowLocalMinutes());
    }, 60_000);
    return () => clearInterval(id);
  }, []);

  const nowHour = Math.floor(nowMin / 60);

  return (
    <div className="flex w-full gap-0">
      {/* 시간 레이블 열 */}
      <div className="relative shrink-0" style={{ width: 46, height: TOTAL_HEIGHT }}>
        {LABEL_HOURS.map(h => (
          <div
            key={h}
            className="absolute right-3 -translate-y-1/2 text-right"
            style={{ top: h * PIXELS_PER_HOUR }}
          >
            <span
              className={cn(
                'text-[10px] tabular-nums font-medium leading-none',
                h === nowHour ? 'text-red-500' : 'text-fg-subtle',
              )}
            >
              {h === 0 ? '자정' : h === 12 ? '정오' : h < 12 ? `${h}시` : `${h - 12}시`}
            </span>
          </div>
        ))}

        {/* 현재 시각 레이블 */}
        <div
          className="absolute right-3 z-20 -translate-y-1/2"
          style={{ top: (nowMin / 60) * PIXELS_PER_HOUR }}
        >
          <div className="flex h-4 items-center justify-center rounded bg-red-500 px-1.5 shadow-sm">
            <span className="text-[9px] font-black leading-none tracking-wider text-white">NOW</span>
          </div>
        </div>
      </div>

      {/* 타임라인 본문 */}
      <div className="relative flex-1" style={{ height: TOTAL_HEIGHT }}>
        {/* 격자선 */}
        {ALL_HOURS.map(h => (
          <div
            key={h}
            className={cn(
              'absolute left-0 right-0 border-t',
              h % 2 === 0 ? 'border-brand/30' : 'border-brand/10',
            )}
            style={{ top: h * PIXELS_PER_HOUR }}
          />
        ))}

        {/* 현재 시각 인디케이터 */}
        <NowIndicator minutes={nowMin} />

        {/* 스케줄 블록 */}
        <div className="absolute inset-0">
          {schedules.map(s => (
            <ScheduleBlock
              key={s.scheduleId}
              schedule={s}
              nowMin={nowMin}
              onToggleActive={onToggleActive}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
