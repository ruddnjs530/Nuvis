import type { ActionModuleType, CreateScheduleRequest, Schedule } from './api/types';
import type { AiScheduleSuggestionData } from './components/ai-schedule-suggestion-card';

import { Loading03Icon, MagicWand01Icon, PlusSignIcon } from '@hugeicons/core-free-icons';
import { useState } from 'react';
import EmptyState from '~/components/common/empty-state';
import Icon from '~/components/common/icon';
import Loading from '~/components/common/loading';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '~/components/ui/sheet';
import {
  useAiScheduleSuggestionsMutation, // 새로 추가
  useCreateScheduleMutation,
  useDeleteScheduleMutation,
  useSchedulesQuery,
  useUpdateScheduleMutation,
} from './api/queries';
import AiScheduleSuggestionCard from './components/ai-schedule-suggestion-card';
import ScheduleDeleteDialog from './components/schedule-delete-dialog';
import ScheduleFormSheet from './components/schedule-form-sheet';

import ScheduleTimeline from './components/schedule-timeline';

function timeToIso(hhmm: string): string {
  return `1970-01-01T${hhmm}:00.000Z`;
}

export default function SchedulesPage() {
  const { data: schedules = [], isLoading } = useSchedulesQuery();
  const createMutation = useCreateScheduleMutation();
  const updateMutation = useUpdateScheduleMutation();
  const deleteMutation = useDeleteScheduleMutation();

  // API 연동 Mutation
  const aiSuggestionMutation = useAiScheduleSuggestionsMutation();

  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scheduleToDelete, setScheduleToDelete] = useState<Schedule | null>(null);

  const [isAiRequested, setIsAiRequested] = useState(false);
  const [isAiPending, setIsAiPending] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<AiScheduleSuggestionData[]>([]);
  const [dismissedSuggestions, setDismissedSuggestions] = useState<string[]>([]);
  const [aiSheetOpen, setAiSheetOpen] = useState(false);

  const visibleSuggestions = aiSuggestions.filter(s => !dismissedSuggestions.includes(s.actionModuleType));

  // --- 실제 API를 호출하는 부분 ---
  const handleRequestAiSuggestion = () => {
    setIsAiRequested(true);
    setIsAiPending(true);
    setDismissedSuggestions([]);

    aiSuggestionMutation.mutate(undefined, {
      onSuccess: (response) => {
        if (response.status === 'success' && response.data) {
          const parsed = Object.values(response.data)
            .filter(value => value.recommended_schedule !== undefined)
            .map(value => ({
              time: value.recommended_schedule!.time,
              actionModuleType: value.recommended_schedule!.actionModuleType.toUpperCase() as ActionModuleType,
              pattern: value.analysis_details?.top_lifestyle_pattern || '라이프스타일 분석',
              reason: value.reason || '패턴 기반 추천입니다.',
            }));

          setAiSuggestions(parsed);

          if (parsed.length > 0) {
            setAiSheetOpen(true);
          }
        }
      },
      onError: (error) => {
        console.error('AI 추천 로드 실패:', error);
        // 필요하다면 에러 토스트 띄우는 로직 추가
      },
      onSettled: () => {
        setIsAiPending(false); // 성공하든 실패하든 로딩 상태 종료
      },
    });
  };

  const handleDismissSuggestion = (moduleType: string) => {
    setDismissedSuggestions(prev => [...prev, moduleType]);
    if (visibleSuggestions.length <= 1) {
      setAiSheetOpen(false);
    }
  };

  const handleAiRecommendClick = (suggestion: AiScheduleSuggestionData) => {
    createMutation.mutate({
      startTime: timeToIso(suggestion.time),
      durationMinutes: 60,
      roomId: 1,
      actionModuleType: suggestion.actionModuleType,
      isActive: true,
    }, {
      onSuccess: () => {
        handleDismissSuggestion(suggestion.actionModuleType);
      },
    });
  };

  const handleCreateClick = () => {
    setSelectedSchedule(null);
    setSheetOpen(true);
  };

  const handleEditClick = (schedule: Schedule) => {
    setSelectedSchedule(schedule);
    setSheetOpen(true);
  };

  const handleDeleteClick = (schedule: Schedule) => {
    setScheduleToDelete(schedule);
    setDeleteDialogOpen(true);
  };

  const handleToggleActive = (schedule: Schedule) => {
    updateMutation.mutate({
      scheduleId: schedule.scheduleId,
      data: {
        roomId: schedule.roomId,
        actionModuleType: schedule.actionModuleType,
        startTime: schedule.startTime,
        durationMinutes: schedule.durationMinutes,
        isActive: !schedule.isActive,
      },
    });
  };

  const handleConfirmDelete = (schedule: Schedule) => {
    deleteMutation.mutate(schedule.scheduleId, {
      onSuccess: () => {
        setDeleteDialogOpen(false);
        setScheduleToDelete(null);
      },
    });
  };

  const handleSave = (data: CreateScheduleRequest) => {
    if (selectedSchedule) {
      updateMutation.mutate({ scheduleId: selectedSchedule.scheduleId, data }, { onSuccess: () => setSheetOpen(false) });
    }
    else {
      createMutation.mutate(data, { onSuccess: () => setSheetOpen(false) });
    }
  };

  if (isLoading) {
    return (
      <div className="relative flex flex-1 flex-col pb-[100px]">
        <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">
          <Loading />
        </main>
      </div>
    );
  }

  return (
    <div className="relative flex flex-1 flex-col pb-[100px] bg-white">
      <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">

        <div className="h-6" />

        <div className="px-4 mb-8 flex flex-col gap-3">
          {!isAiRequested && (
            <button
              type="button"
              onClick={handleRequestAiSuggestion}
              className="group flex w-full items-center justify-between gap-3 rounded-2xl border border-brand/10 bg-brand-subtle/50 px-5 py-3 transition-all hover:border-brand/20 hover:bg-brand-subtle"
            >
              <div className="flex items-center gap-2.5 text-brand">
                <Icon icon={MagicWand01Icon} size="sm" color="currentColor" />
                <span className="text-sm font-bold tracking-tight">AI 맞춤 스케줄 추천 받기</span>
              </div>
              <span className="text-xs text-brand/70 font-medium group-hover:text-brand">최근 주거 패턴 분석</span>
            </button>
          )}

          {isAiPending && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border-default bg-surface px-5 py-6 text-fg-muted shadow-inner">
              <Icon icon={Loading03Icon} size="md" color="currentColor" className="animate-spin text-brand/60" />
              <span className="text-sm font-medium">유저님의 생활 패턴을 분석하고 있습니다...</span>
            </div>
          )}

          {isAiRequested && !isAiPending && visibleSuggestions.length > 0 && (
            <button
              type="button"
              onClick={() => setAiSheetOpen(true)}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-brand/5 px-5 py-3 text-sm font-bold text-brand transition-colors hover:bg-brand/10"
            >
              <Icon icon={MagicWand01Icon} size="sm" color="currentColor" />
              확인하지 않은 AI 추천 스케줄이
              {' '}
              {visibleSuggestions.length}
              개 있습니다
            </button>
          )}

          {isAiRequested && !isAiPending && visibleSuggestions.length === 0 && (
            <div className="text-center text-xs text-fg-subtle pt-1 animate-in fade-in duration-300">
              모든 추천을 확인했습니다. 새로운 패턴이 생기면 다시 알려드릴게요.
            </div>
          )}
        </div>

        <div className="px-4 pb-4">
          {schedules.length === 0
            ? (
                <EmptyState title="등록된 스케줄이 없습니다." description="우측 하단의 + 버튼을 눌러 새 스케줄을 등록해 보세요." />
              )
            : (
                <ScheduleTimeline
                  schedules={schedules}
                  onToggleActive={handleToggleActive}
                  onEdit={handleEditClick}
                  onDelete={handleDeleteClick}
                />
              )}
        </div>
      </main>

      <div className="fixed bottom-[96px] left-1/2 z-40 mx-auto w-full max-w-[448px] -translate-x-1/2 px-4">
        <button
          type="button"
          onClick={handleCreateClick}
          className="absolute bottom-0 right-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lg transition-transform hover:scale-105 active:scale-95"
        >
          <Icon icon={PlusSignIcon} size="md" color="currentColor" />
        </button>
      </div>

      <Sheet open={aiSheetOpen} onOpenChange={setAiSheetOpen}>
        <SheetContent side="bottom" className="max-h-[85dvh] overflow-y-auto rounded-t-3xl px-5 pb-10 pt-6 bg-surface">
          <SheetHeader className="mb-6">
            <SheetTitle className="text-left text-xl font-bold text-fg-strong flex items-center gap-2">
              <Icon icon={MagicWand01Icon} size="sm" color="brand" />
              AI 맞춤 스케줄 제안
            </SheetTitle>
          </SheetHeader>

          <div className="flex flex-col gap-4">
            <p className="text-sm text-fg-muted -mt-2">카드를 탭하면 즉시 스케줄이 등록됩니다.</p>
            {visibleSuggestions.map(suggestion => (
              <AiScheduleSuggestionCard
                key={suggestion.actionModuleType}
                suggestion={suggestion}
                onClick={handleAiRecommendClick}
                onDismiss={() => handleDismissSuggestion(suggestion.actionModuleType)}
              />
            ))}
          </div>
        </SheetContent>
      </Sheet>

      <ScheduleFormSheet
        key={selectedSchedule?.scheduleId ?? 'new'}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        schedule={selectedSchedule}
        onSave={handleSave}
      />

      <ScheduleDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        schedule={scheduleToDelete}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
