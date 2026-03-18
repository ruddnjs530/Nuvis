import { BaseEntity } from '../common/base.entity';
import { ThresholdVO } from './vo/threshold.vo';

export interface AiSuggestionProps {
  eventId: number;
  suggestedThreshold: ThresholdVO;
  reason: string;
  status: string; // e.g. 'PENDING', 'ACCEPTED', 'REJECTED'
  createdAt: Date;
}

export class AiSuggestion extends BaseEntity<number> {
  private props: AiSuggestionProps;

  private constructor(id: number, props: AiSuggestionProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: AiSuggestionProps): AiSuggestion {
    return new AiSuggestion(id || 0, props);
  }

  get eventId(): number { return this.props.eventId; }
  get suggestedThreshold(): ThresholdVO { return this.props.suggestedThreshold; }
  get reason(): string { return this.props.reason; }
  get status(): string { return this.props.status; }
  get createdAt(): Date { return this.props.createdAt; }

  public accept(): void { this.props.status = 'ACCEPTED'; }
  public reject(): void { this.props.status = 'REJECTED'; }
}
