import type { EventResponse } from './api/types';

import type { EventItem } from './components/event-card';

import type { EventFormData } from './components/event-form-sheet';
import { PlusSignIcon } from '@hugeicons/core-free-icons';

import { useState } from 'react';
import EmptyState from '~/components/common/empty-state';
import Icon from '~/components/common/icon';
import Loading from '~/components/common/loading';
import SectionHeader from '~/components/common/section-header';
import {
  useCreateEventMutation,
  useDeleteEventMutation,
  useEventsQuery,
  useUpdateEventMutation,
} from './api/queries';
import EventCard from './components/event-card';
import EventDeleteDialog from './components/event-delete-dialog';
import EventFormSheet from './components/event-form-sheet';

// Mock DB -> UI Mapper
function mapEventResponseToItem(apiEvent: EventResponse): EventItem {
  const roomName = apiEvent.roomId === 1 ? '부엌' : apiEvent.roomId === 2 ? '침실' : '거실';
  const deviceName = apiEvent.actionModuleType === 'AIR_PURIFIER' ? '공기 청정기' : apiEvent.actionModuleType === 'HUMIDIFIER' ? '가습기' : '모듈';
  const conditionName = apiEvent.conditionType === 'FINE_DUST' ? '미세먼지' : apiEvent.conditionType === 'HUMIDITY' ? '습도' : '조건';
  const operatorText = apiEvent.conditionOperator === 'GT' ? '이상' : apiEvent.conditionOperator === 'LT' ? '이하' : '일치';

  return {
    id: String(apiEvent.eventId),
    room: roomName,
    deviceName,
    active: apiEvent.isActive,
    conditionStr: `${conditionName}가 ${apiEvent.thresholdValue} ${operatorText}`,
  };
}

export default function EventsPage() {
  // API Hooks
  const { data: rawEvents = [], isLoading } = useEventsQuery();
  const createMutation = useCreateEventMutation();
  const updateMutation = useUpdateEventMutation();
  const deleteMutation = useDeleteEventMutation();

  const events = rawEvents.map(mapEventResponseToItem).concat([{
    id: '1',
    room: '테스트 장소',
    deviceName: '공기 청정기',
    active: true,
    conditionStr: '미세먼지가 100 이상',
  }]);

  // Sheet & Dialog State
  const [sheetOpen, setSheetOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);

  // Handlers
  const handleToggle = (id: string, active: boolean) => {
    updateMutation.mutate({ eventId: Number(id), data: { isActive: active } });
  };

  const handleEditClick = (ev: EventItem) => {
    setSelectedEvent(ev);
    setSheetOpen(true);
  };

  const handleDeleteClick = (ev: EventItem) => {
    setSelectedEvent(ev);
    setDialogOpen(true);
  };

  const handleCreateClick = () => {
    setSelectedEvent(null);
    setSheetOpen(true);
  };

  const handleSaveEvent = (formData: EventFormData) => {
    if (!formData.id) {
      createMutation.mutate({
        roomId: formData.roomId,
        conditionType: formData.conditionType,
        conditionOperator: formData.conditionOperator,
        thresholdValue: formData.thresholdValue,
        actionModuleType: formData.actionModuleType,
        isActive: true,
      }, {
        onSuccess: () => setSheetOpen(false),
      });
    }
    else {
      updateMutation.mutate({
        eventId: Number(formData.id),
        data: {
          roomId: formData.roomId,
          conditionType: formData.conditionType,
          conditionOperator: formData.conditionOperator,
          actionModuleType: formData.actionModuleType,
          thresholdValue: formData.thresholdValue,
          isActive: formData.isActive,
        },
      }, {
        onSuccess: () => setSheetOpen(false),
      });
    }
  };

  const handleConfirmDelete = (deletedEvent: EventItem) => {
    deleteMutation.mutate(Number(deletedEvent.id), {
      onSuccess: () => setDialogOpen(false),
    });
  };

  if (isLoading) {
    return (
      <div className="relative flex flex-1 flex-col pb-[100px]">
        <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">
          <SectionHeader>등록된 이벤트</SectionHeader>
          <Loading />
        </main>
      </div>
    );
  }

  return (
    <div className="relative flex flex-1 flex-col pb-[100px]">

      <main className="mx-auto flex w-full max-w-[448px] flex-1 flex-col pb-8">
        {/* <SectionHeader>등록된 이벤트</SectionHeader> */}

        <div className="h-4" />

        <div className="flex flex-col gap-4 px-4">
          {events.length === 0
            ? (
                <EmptyState title="등록된 이벤트가 없습니다." description="우측 하단의 + 버튼을 눌러 새 이벤트를 등록해 보세요." />
              )
            : (
                events.map(ev => (
                  <EventCard
                    key={ev.id}
                    event={ev}
                    onToggle={handleToggle}
                    onEdit={handleEditClick}
                    onDelete={handleDeleteClick}
                  />
                ))
              )}
        </div>
      </main>

      {/* FAB */}
      <div className="fixed bottom-[96px] left-1/2 z-40 mx-auto w-full max-w-[448px] -translate-x-1/2 px-4">
        <button
          type="button"
          onClick={handleCreateClick}
          className="absolute bottom-0 right-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lg transition-transform hover:scale-105 active:scale-95"
          aria-label="새 이벤트 등록"
        >
          <Icon icon={PlusSignIcon} size="md" color="currentColor" strokeWidth={2} />
        </button>
      </div>

      <EventFormSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        event={selectedEvent}
        onSave={handleSaveEvent}
      />

      <EventDeleteDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        event={selectedEvent}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
