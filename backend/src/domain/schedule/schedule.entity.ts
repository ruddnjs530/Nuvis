import { BaseEntity } from '../common/base.entity';
import { DurationVO } from './vo/duration.vo';

export interface ScheduleProps {
  userId: number;
  roomId: number;
  actionModuleType: string;
  startTime: Date;
  duration: DurationVO;
  isActive: boolean;
}

export class Schedule extends BaseEntity<number> {
  private props: ScheduleProps;

  private constructor(id: number, props: ScheduleProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: ScheduleProps): Schedule {
    return new Schedule(id || 0, props);
  }

  get userId(): number { return this.props.userId; }
  get roomId(): number { return this.props.roomId; }
  get actionModuleType(): string { return this.props.actionModuleType; }
  get startTime(): Date { return this.props.startTime; }
  get duration(): DurationVO { return this.props.duration; }
  get isActive(): boolean { return this.props.isActive; }

  public activate(): void {
    this.props.isActive = true;
  }

  public deactivate(): void {
    this.props.isActive = false;
  }
}
