import { Cancel01Icon, Edit01Icon, GridViewIcon } from '@hugeicons/core-free-icons';
import AppCard from '~/components/common/app-card';
import Icon from '~/components/common/icon';
import { Switch } from '~/components/ui/switch';

export interface EventItem {
  id: string;
  room: string;
  deviceName: string;
  active: boolean;
  conditionStr: string;
}

interface EventCardProps {
  event: EventItem;
  onToggle: (id: string, active: boolean) => void;
  onEdit: (event: EventItem) => void;
  onDelete: (event: EventItem) => void;
}

export default function EventCard({ event, onToggle, onEdit, onDelete }: EventCardProps) {
  return (
    <AppCard className="flex flex-col gap-4 p-5">
      {/* Header: Icon, Info, Switch */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Icon Circle */}
          <div className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-full bg-brand-subtle text-brand">
            <Icon icon={GridViewIcon} size="md" color="brand" strokeWidth={2} />
          </div>
          {/* Device Info */}
          <div className="flex flex-col">
            <span className="text-xs text-fg-muted">{event.room}</span>
            <span className="text-base font-bold text-fg-strong">{event.deviceName}</span>
          </div>
        </div>

        <Switch
          checked={event.active}
          onCheckedChange={checked => onToggle(event.id, checked)}
        />
      </div>

      {/* Condition Block */}
      <div className="flex items-center gap-3 rounded-lg bg-surface-sunken px-4 py-3">
        <span className="text-sm font-black text-brand">IF</span>
        <span className="text-sm text-brand">{event.conditionStr}</span>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-end gap-5 pt-1">
        <button
          type="button"
          onClick={() => onEdit(event)}
          className="flex items-center gap-1.5 text-sm text-fg-default transition-colors hover:text-fg-strong"
        >
          <Icon icon={Edit01Icon} size="xs" color="currentColor" strokeWidth={2} />
          <span>수정</span>
        </button>
        <button
          type="button"
          onClick={() => onDelete(event)}
          className="flex items-center gap-1.5 text-sm text-fg-default transition-colors hover:text-red-500"
        >
          <Icon icon={Cancel01Icon} size="xs" color="currentColor" strokeWidth={2} />
          <span>삭제</span>
        </button>
      </div>
    </AppCard>
  );
}
