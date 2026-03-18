import { BaseEntity } from '../common/base.entity';
import { ThresholdVO } from './vo/threshold.vo';

export interface EventProps {
  userId: number;
  roomId: number;
  conditionType: string;
  conditionOperator: string;
  threshold: ThresholdVO;
  actionModuleType: string;
  isActive: boolean;
}

export class Event extends BaseEntity<number> {
  private props: EventProps;

  private constructor(id: number, props: EventProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: EventProps): Event {
    return new Event(id || 0, props);
  }

  get userId(): number { return this.props.userId; }
  get roomId(): number { return this.props.roomId; }
  get conditionType(): string { return this.props.conditionType; }
  get conditionOperator(): string { return this.props.conditionOperator; }
  get threshold(): ThresholdVO { return this.props.threshold; }
  get actionModuleType(): string { return this.props.actionModuleType; }
  get isActive(): boolean { return this.props.isActive; }

  public activate(): void { this.props.isActive = true; }
  public deactivate(): void { this.props.isActive = false; }
  public updateThreshold(t: ThresholdVO): void { this.props.threshold = t; }
}
