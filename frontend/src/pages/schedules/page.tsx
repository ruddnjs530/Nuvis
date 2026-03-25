import type { CreateScheduleRequest, Schedule } from './api/types';
import { PlusSignIcon } from '@hugeicons/core-free-icons';
import { useState } from 'react';
import EmptyState from '~/components/common/empty-state';
import Icon from '~/components/common/icon';
import Loading from '~/components/common/loading';
import {
  useCreateScheduleMutation,
  useDeleteScheduleMutation,
  useSchedulesQuery,
  useUpdateScheduleMutation,
} from './api/queries';
import ScheduleDeleteDialog from './components/schedule-delete-dialog';
import ScheduleFormSheet from './components/schedule-form-sheet';
import ScheduleTimeline from './components/schedule-timeline';

export default function SchedulesPage() {
  const { data: schedules = [], isLoading } = useSchedulesQuery();
  const createMutation = useCreateScheduleMutation();
  const updateMutation = useUpdateScheduleMutation();
  const deleteMutation = useDeleteScheduleMutation();

  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scheduleToDelete, setScheduleToDelete] = useState<Schedule | null>(null);

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
      updateMutation.mutate(
        { scheduleId: selectedSchedule.scheduleId, data },
        { onSuccess: () => setSheetOpen(false) },
      );
    }
    else {
      createMutation.mutate(data, { onSuccess: () => setSheetOpen(false) });
    }
  };

  if (isLoading) {
    return (
      <div className="relative flex flex-1 flex-col pb-[100px]">
        <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">
          {/* <SectionHeader>스케줄</SectionHeader> */}
          <Loading />
        </main>
      </div>
    );
  }

  return (
    <div className="relative flex flex-1 flex-col pb-[100px]">
      <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">
        {/* <SectionHeader>스케줄</SectionHeader> */}

        <div className="h-12" />

        <div className="px-4 pb-4">
          {schedules.length === 0
            ? (
                <EmptyState
                  title="등록된 스케줄이 없습니다."
                  description="우측 하단의 + 버튼을 눌러 새 스케줄을 등록해 보세요."
                />
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

      {/* FAB */}
      <div className="fixed bottom-[96px] left-1/2 z-40 mx-auto w-full max-w-[448px] -translate-x-1/2 px-4">
        <button
          type="button"
          onClick={handleCreateClick}
          className="absolute bottom-0 right-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lg transition-transform hover:scale-105 active:scale-95"
          aria-label="새 스케줄 등록"
        >
          <Icon icon={PlusSignIcon} size="md" color="currentColor" strokeWidth={2} />
        </button>
      </div>

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
