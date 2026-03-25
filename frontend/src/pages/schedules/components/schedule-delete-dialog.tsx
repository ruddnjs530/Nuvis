import type { Schedule } from '../api/types';
import { Button } from '~/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';

const MODULE_LABELS: Record<string, string> = {
  AIR_PURIFIER: '공기청정기',
  HUMIDIFIER: '가습기',
};

const ROOM_LABELS: Record<number, string> = {
  1: '거실',
  2: '침실',
  3: '부엌',
};

interface ScheduleDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schedule: Schedule | null;
  onConfirm: (schedule: Schedule) => void;
}

export default function ScheduleDeleteDialog({ open, onOpenChange, schedule, onConfirm }: ScheduleDeleteDialogProps) {
  if (!schedule)
    return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[90%] max-w-sm rounded-[24px] p-6" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle className="text-center text-lg font-bold">스케줄 삭제</DialogTitle>
          <DialogDescription className="pt-3 text-center text-sm text-fg-default">
            '
            {ROOM_LABELS[schedule.roomId] ?? '알 수 없는 곳'}
            {' '}
            {MODULE_LABELS[schedule.actionModuleType] ?? schedule.actionModuleType}
            '
            <br />
            스케줄을 정말 삭제하시겠습니까?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-6 flex flex-row gap-3">
          <Button variant="outline" className="h-12 flex-1 rounded-xl" onClick={() => onOpenChange(false)}>
            취소
          </Button>
          <Button
            className="h-12 flex-1 rounded-xl bg-red-500 text-white hover:bg-red-600"
            onClick={() => onConfirm(schedule)}
          >
            삭제
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
