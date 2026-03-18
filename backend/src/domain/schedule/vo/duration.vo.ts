import { IsNumber, Min } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface DurationProps {
  value: number; // in minutes
}

export class DurationVO extends ValueObject<DurationProps> {
  @IsNumber()
  @Min(1, { message: 'Duration must be at least 1 minute' })
  private readonly durationValue: number;

  private constructor(props: DurationProps) {
    super(props);
    this.durationValue = props.value;
    this.validate();
  }

  public static create(minutes: number): DurationVO {
    return new DurationVO({ value: minutes });
  }

  get value(): number {
    return this.props.value;
  }
}
