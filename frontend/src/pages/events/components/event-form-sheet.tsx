import type { ActionModuleType, ConditionOperator, ConditionType } from '../api/types';
import type { EventItem } from './event-card';
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

export interface EventFormData {
  id?: string;
  roomId: number;
  actionModuleType: ActionModuleType;
  conditionType: ConditionType;
  conditionOperator: ConditionOperator;
  thresholdValue: number;
  isActive: boolean;
}

interface EventFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event: EventItem | null;
  onSave: (data: EventFormData) => void;
}

// Mock Data for Options
const ROOM_OPTIONS = [
  { id: 2, label: '거실' },
  { id: 5, label: '침실' },
  { id: 4, label: '부엌' },
];

const DEVICE_OPTIONS = [
  { id: 'AIR_PURIFIER', label: '공기 청정기' },
  { id: 'HUMIDIFIER', label: '가습기' },
];

const CONDITION_TYPES = [
  { id: 'FINE_DUST', label: '미세먼지' },
  { id: 'HUMIDITY', label: '습도' },
  { id: 'TEMPERATURE', label: '온도' },
];

const CONDITION_OPERATORS = [
  { id: 'GT', label: '이상' },
  { id: 'EQ', label: '일치' },
  { id: 'LT', label: '이하' },
];

const CONDITION_MAPPING: Record<string, string[]> = {
  AIR_PURIFIER: ['FINE_DUST'],
  HUMIDIFIER: ['HUMIDITY'],
};

const NUMBER_REGEX = /\d+/;

// Helper UI component for chip rendering
function Chip({ active, label, onClick, disabled }: { active: boolean; label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      onClick={!disabled ? onClick : undefined}
      disabled={disabled}
      className={cn(
        'rounded-full px-4 py-2 text-sm font-medium transition-colors border',
        active
          ? 'bg-brand text-white border-brand'
          : 'bg-surface border-border-default text-fg-muted hover:bg-surface-sunken',
        disabled && 'opacity-50 cursor-not-allowed',
      )}
    >
      {label}
    </button>
  );
}

export default function EventFormSheet({ open, onOpenChange, event, onSave }: EventFormSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="rounded-t-3xl p-0 max-h-[90dvh] flex flex-col">
        {open && (
          <EventFormContent
            key={event ? event.id : 'new'}
            onOpenChange={onOpenChange}
            event={event}
            onSave={onSave}
          />
        )}
      </SheetContent>
    </Sheet>
  );
}

function EventFormContent({ onOpenChange, event, onSave }: Omit<EventFormSheetProps, 'open'>) {
  const isEdit = !!event;

  // 1. Initialize state directly from props, completely removing useEffect!
  const [currentStep, setCurrentStep] = useState<1 | 2>(1);
  const [roomId, setRoomId] = useState<number>(() => event?.room === '침실' ? 2 : event?.room === '거실' ? 3 : 1);
  const [actionModuleType, setActionModuleType] = useState<ActionModuleType>(() => event?.deviceName === '가습기' ? 'HUMIDIFIER' : 'AIR_PURIFIER');
  const [conditionType, setConditionType] = useState<ConditionType>(() => event?.conditionStr.includes('습도') ? 'HUMIDITY' : event?.conditionStr.includes('온도') ? 'TEMPERATURE' : 'FINE_DUST');
  const [conditionOperator, setConditionOperator] = useState<ConditionOperator>(() => event?.conditionStr.includes('이하') ? 'LT' : event?.conditionStr.includes('일치') ? 'EQ' : 'GT');
  const [thresholdValue, setThresholdValue] = useState<number>(() => {
    if (!event)
      return 100;
    const numMatch = event.conditionStr.match(NUMBER_REGEX);
    return numMatch ? Number.parseInt(numMatch[0], 10) : 100;
  });

  const handleNext = () => {
    // When moving to Step 2, auto-select a valid condition if the current one is mismatched
    const allowedConditions = CONDITION_MAPPING[actionModuleType] || CONDITION_TYPES.map(c => c.id);
    if (!allowedConditions.includes(conditionType)) {
      setConditionType(allowedConditions[0] as ConditionType);
    }
    setCurrentStep(2);
  };

  const handleSave = () => {
    onSave({
      id: event ? event.id : undefined,
      roomId,
      actionModuleType,
      conditionType,
      conditionOperator,
      thresholdValue,
      isActive: event ? event.active : true,
    });
  };

  return (
    <>
      {/* Floating Stepper Badge (Outside the Sheet) */}
      <div className="absolute -top-14 left-0 right-0 flex justify-center">
        <div className="rounded-full bg-surface px-5 py-1.5 text-sm font-bold shadow-md text-brand">
          Step
          {' '}
          {currentStep}
          {' '}
          <span className="text-fg-muted font-normal">/ 2</span>
        </div>
      </div>

      <SheetHeader className="p-8 pb-4 shrink-0">
        <SheetTitle className="text-left text-2xl font-bold">
          {isEdit ? '이벤트 수정' : '새 이벤트 등록'}
        </SheetTitle>
      </SheetHeader>

      {/* Scrollable Form Content */}
      <div className="flex-1 overflow-y-auto min-h-0 px-8 py-6 flex flex-col gap-10">

        {currentStep === 1 && (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-right-4 duration-300">
            <section className="flex flex-col gap-3">
              <h3 className="font-bold text-fg-strong">어디로 보낼까요?</h3>
              <div className="flex flex-wrap gap-2">
                {ROOM_OPTIONS.map(opt => (
                  <Chip
                    key={opt.id}
                    active={roomId === opt.id}
                    label={opt.label}
                    onClick={() => setRoomId(opt.id)}
                  />
                ))}
              </div>
            </section>

            <section className="flex flex-col gap-3">
              <h3 className="font-bold text-fg-strong">어떤 기기를 작동시킬까요?</h3>
              <div className="flex flex-wrap gap-2">
                {DEVICE_OPTIONS.map(opt => (
                  <Chip
                    key={opt.id}
                    active={actionModuleType === opt.id}
                    label={opt.label}
                    onClick={() => setActionModuleType(opt.id as ActionModuleType)}
                  />
                ))}
              </div>
            </section>
          </div>
        )}

        {currentStep === 2 && (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-right-4 duration-300">
            <section className="flex flex-col gap-5">
              <h3 className="font-bold text-fg-strong">언제 작동시킬까요?</h3>

              <div className="flex flex-col gap-2">
                <span className="text-xs text-fg-muted">조건 센서</span>
                <div className="flex flex-wrap gap-2">
                  {CONDITION_TYPES
                    .filter(c => (CONDITION_MAPPING[actionModuleType] || CONDITION_TYPES.map(x => x.id)).includes(c.id))
                    .map(opt => (
                      <Chip
                        key={opt.id}
                        active={conditionType === opt.id}
                        label={opt.label}
                        onClick={() => setConditionType(opt.id as ConditionType)}
                      />
                    ))}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-xs text-fg-muted">임계 수치</span>
                <div className="flex items-center justify-between rounded-xl bg-surface p-3 border border-border-default">
                  <button
                    type="button"
                    onClick={() => setThresholdValue(prev => Math.max(0, prev - 5))}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-sunken text-xl text-brand transition-colors hover:bg-brand-subtle"
                  >
                    <Icon icon={MinusSignIcon} />
                  </button>
                  <div className="text-2xl font-bold text-fg-strong tracking-tight">
                    {thresholdValue}
                  </div>
                  <button
                    type="button"
                    onClick={() => setThresholdValue(prev => prev + 5)}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-sunken text-xl text-brand transition-colors hover:bg-brand-subtle"
                  >
                    <Icon icon={PlusSignIcon} />
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-xs text-fg-muted">작동 방식</span>
                <div className="flex flex-wrap gap-2">
                  {CONDITION_OPERATORS.map(opt => (
                    <Chip
                      key={opt.id}
                      active={conditionOperator === opt.id}
                      label={opt.label}
                      onClick={() => setConditionOperator(opt.id as ConditionOperator)}
                    />
                  ))}
                </div>
              </div>

            </section>
          </div>
        )}

      </div>

      {/* Fixed Footer */}
      <div className="shrink-0 p-8 pt-6 border-t border-border-muted bg-surface flex gap-3">
        {currentStep === 1
          ? (
              <>
                <Button variant="outline" size="xl" className="flex-1" onClick={() => onOpenChange(false)}>
                  취소
                </Button>
                <Button
                  variant="brand"
                  size="xl"
                  className="flex-1"
                  onClick={handleNext}
                >
                  다음
                </Button>
              </>
            )
          : (
              <>
                <Button variant="outline" size="xl" className="flex-1" onClick={() => setCurrentStep(1)}>
                  이전
                </Button>
                <Button
                  variant="brand"
                  size="xl"
                  className="flex-1"
                  onClick={handleSave}
                >
                  저장하기
                </Button>
              </>
            )}
      </div>
    </>
  );
}
