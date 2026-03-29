import type {
  ActionModuleType,
  Schedule,
} from './api/types';
import type { AiScheduleSuggestionData } from './components/ai-schedule-suggestion-card';
import {
  Loading03Icon,
  MagicWand01Icon,
  PlusSignIcon,
} from '@hugeicons/core-free-icons';
import { useState } from 'react';
import EmptyState from '~/components/common/empty-state';
import Icon from '~/components/common/icon';
import Loading from '~/components/common/loading';
import SectionHeader from '~/components/common/section-header';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '~/components/ui/sheet';
import {
  useAiScheduleSuggestionsMutation,
  useCreateScheduleMutation,
  useDeleteScheduleMutation,
  useSchedulesQuery,
  useUpdateScheduleMutation,
} from './api/queries';
import AiScheduleSuggestionCard from './components/ai-schedule-suggestion-card';
import ScheduleDeleteDialog from './components/schedule-delete-dialog';
import ScheduleFormSheet from './components/schedule-form-sheet';

import ScheduleTimeline from './components/schedule-timeline';

// --- API 응답 타입 정의 (카멜 케이스) ---
interface AiDeviceResponse {
  recommendedSchedule?: {
    time: string;
    actionModuleType: string;
    action: string;
  };
  analysisDetails?: {
    topLifestylePattern: string;
    [key: string]: any;
  };
  reason?: string;
  message?: string;
}

interface AiRoomData {
  roomId: number;
  recordsAnalyzed: number;
  suggestions: Record<string, AiDeviceResponse>;
}

interface AiResponse {
  status: string;
  userId: number;
  data: Record<string, AiRoomData>;
}

// --- 헬퍼 함수 ---
function timeToIso(hhmm: string) {
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

  const visibleSuggestions = aiSuggestions.filter((s) => {
    return !dismissedSuggestions.includes(`${s.roomId}-${s.actionModuleType}`);
  });

  // --- 핸들러: AI 추천 요청 ---
  const handleRequestAiSuggestion = () => {
    setIsAiRequested(true);
    setIsAiPending(true);
    setDismissedSuggestions([]);

    aiSuggestionMutation.mutate(undefined, {
      onSuccess: (response: AiResponse | any) => {
        if (response.status === 'success' && response.data) {
          const parsed: AiScheduleSuggestionData[] = [];

          Object.values(response.data).forEach((roomData: any) => {
            if (roomData.suggestions) {
              Object.values(roomData.suggestions).forEach((deviceInfo: any) => {
                if (deviceInfo.recommendedSchedule) {
                  parsed.push({
                    time: deviceInfo.recommendedSchedule.time,
                    actionModuleType: deviceInfo.recommendedSchedule.actionModuleType.toUpperCase() as ActionModuleType,
                    roomId: roomData.roomId,
                    pattern:
                      deviceInfo.analysisDetails?.topLifestylePattern
                      || '라이프스타일 분석',
                    reason: deviceInfo.reason || '패턴 기반 추천입니다.',
                  });
                }
              });
            }
          });

          setAiSuggestions(parsed);

          if (parsed.length > 0) {
            setAiSheetOpen(true);
          }
        }
      },
      onSettled: () => {
        setIsAiPending(false);
      },
    });
  };

  // --- 핸들러: 추천 카드 클릭 (즉시 등록) ---
  const handleAiRecommendClick = (suggestion: AiScheduleSuggestionData) => {
    createMutation.mutate(
      {
        startTime: timeToIso(suggestion.time),
        durationMinutes: 60,
        roomId: suggestion.roomId,
        actionModuleType: suggestion.actionModuleType,
        isActive: true,
      },
      {
        onSuccess: () => {
          setDismissedSuggestions((prev) => {
            return [...prev, `${suggestion.roomId}-${suggestion.actionModuleType}`];
          });
          if (visibleSuggestions.length <= 1) {
            setAiSheetOpen(false);
          }
        },
      },
    );
  };

  if (isLoading) {
    return (
      <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8 px-4">
        <SectionHeader>등록된 스케줄</SectionHeader>
        <Loading />
      </main>
    );
  }

  return (
    <div className="relative flex flex-1 flex-col pb-[100px] bg-white">
      <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">
        <div className="h-6" />

        {/* AI 추천 영역 */}
        <div className="px-4 mb-8 flex flex-col gap-3">
          {!isAiRequested && (
            <button
              type="button"
              onClick={handleRequestAiSuggestion}
              className="group flex w-full items-center justify-between gap-3 rounded-2xl border border-brand/10 bg-brand-subtle/50 px-5 py-3 transition-all hover:bg-brand-subtle"
            >
              <div className="flex items-center gap-2.5 text-brand">
                <Icon icon={MagicWand01Icon} size="sm" color="currentColor" />
                <span className="text-sm font-bold">
                  AI 맞춤 스케줄 추천 받기
                </span>
              </div>
              <span className="text-xs text-brand/70 font-medium">
                패턴 분석
              </span>
            </button>
          )}

          {isAiPending && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border bg-surface px-5 py-6 text-fg-muted shadow-inner">
              <Icon
                icon={Loading03Icon}
                size="md"
                color="currentColor"
                className="animate-spin text-brand/60"
              />
              <span className="text-sm font-medium">패턴을 분석 중입니다...</span>
            </div>
          )}

          {isAiRequested && !isAiPending && visibleSuggestions.length > 0 && (
            <button
              type="button"
              onClick={() => {
                setAiSheetOpen(true);
              }}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-brand/5 px-5 py-3 text-sm font-bold text-brand transition-colors hover:bg-brand/10"
            >
              <Icon icon={MagicWand01Icon} size="sm" color="currentColor" />
              확인하지 않은 추천
              {' '}
              {visibleSuggestions.length}
              개 보기
            </button>
          )}
        </div>

        <div className="px-4">
          <SectionHeader>나의 자동화 조건</SectionHeader>
        </div>

        <div className="px-4 pb-4">
          {schedules.length === 0
            ? (
                <EmptyState
                  title="등록된 스케줄이 없습니다."
                  description="+ 버튼을 눌러 등록해 보세요."
                />
              )
            : (
                <ScheduleTimeline
                  schedules={schedules}
                  onToggleActive={(s) => {
                    updateMutation.mutate({
                      scheduleId: s.scheduleId,
                      data: { ...s, isActive: !s.isActive },
                    });
                  }}
                  onEdit={(s) => {
                    setSelectedSchedule(s);
                    setSheetOpen(true);
                  }}
                  onDelete={(s) => {
                    setScheduleToDelete(s);
                    setDeleteDialogOpen(true);
                  }}
                />
              )}
        </div>
      </main>

      {/* FAB */}
      <div className="fixed bottom-[96px] left-1/2 z-40 mx-auto w-full max-w-[448px] -translate-x-1/2 px-4">
        <button
          type="button"
          onClick={() => {
            setSelectedSchedule(null);
            setSheetOpen(true);
          }}
          className="absolute bottom-0 right-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-xl transition-transform hover:scale-110 active:scale-95"
        >
          <Icon icon={PlusSignIcon} size="md" color="currentColor" />
        </button>
      </div>

      {/* AI 추천 바텀 시트 */}
      <Sheet open={aiSheetOpen} onOpenChange={setAiSheetOpen}>
        <SheetContent
          side="bottom"
          className="max-h-[85dvh] overflow-y-auto rounded-t-3xl px-5 pb-10 pt-6 bg-surface"
        >
          <SheetHeader className="mb-6">
            <SheetTitle className="text-left text-xl font-bold flex items-center gap-2">
              <Icon icon={MagicWand01Icon} size="sm" color="brand" />
              AI 맞춤 스케줄 제안
            </SheetTitle>
          </SheetHeader>
          <div className="flex flex-col gap-4">
            <p className="text-sm text-fg-muted -mt-2">
              카드를 탭하면 즉시 등록됩니다.
            </p>
            {visibleSuggestions.map((s) => {
              return (
                <AiScheduleSuggestionCard
                  key={`${s.roomId}-${s.actionModuleType}`}
                  suggestion={s}
                  onClick={handleAiRecommendClick}
                  onDismiss={() => {
                    setDismissedSuggestions((p) => {
                      return [...p, `${s.roomId}-${s.actionModuleType}`];
                    });
                    if (visibleSuggestions.length <= 1) {
                      setAiSheetOpen(false);
                    }
                  }}
                />
              );
            })}
          </div>
        </SheetContent>
      </Sheet>

      {/* 수동 등록 폼 시트 */}
      <ScheduleFormSheet
        key={selectedSchedule?.scheduleId ?? 'new'}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        schedule={selectedSchedule}
        onSave={(data) => {
          if (selectedSchedule) {
            updateMutation.mutate(
              { scheduleId: selectedSchedule.scheduleId, data },
              {
                onSuccess: () => {
                  setSheetOpen(false);
                },
              },
            );
          }
          else {
            createMutation.mutate(data, {
              onSuccess: () => {
                setSheetOpen(false);
              },
            });
          }
        }}
      />

      {/* 삭제 확인 다이얼로그 */}
      <ScheduleDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        schedule={scheduleToDelete}
        onConfirm={(s) => {
          deleteMutation.mutate(s.scheduleId, {
            onSuccess: () => {
              setDeleteDialogOpen(false);
            },
          });
        }}
      />
    </div>
  );
}
