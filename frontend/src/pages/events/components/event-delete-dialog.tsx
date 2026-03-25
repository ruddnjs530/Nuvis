import type { EventItem } from './event-card';
import { Button } from '~/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';

interface EventDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event: EventItem | null;
  onConfirm: (event: EventItem) => void;
}

export default function EventDeleteDialog({ open, onOpenChange, event, onConfirm }: EventDeleteDialogProps) {
  if (!event)
    return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[90%] max-w-sm rounded-[24px] p-6" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle className="text-center text-lg font-bold">이벤트 삭제</DialogTitle>
          <DialogDescription className="pt-3 text-center text-sm text-fg-default">
            '
            {event.room}
            {' '}
            {event.deviceName}
            '
            <br />
            조건을 정말 삭제하시겠습니까?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-6 flex flex-row gap-3">
          <Button variant="outline" className="h-12 flex-1 rounded-xl" onClick={() => onOpenChange(false)}>
            취소
          </Button>
          <Button
            className="h-12 flex-1 rounded-xl bg-red-500 text-white hover:bg-red-600"
            onClick={() => onConfirm(event)}
          >
            삭제
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
