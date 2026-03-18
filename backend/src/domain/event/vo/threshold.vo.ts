import { IsNumber } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface ThresholdProps {
  value: number;
}

export class ThresholdVO extends ValueObject<ThresholdProps> {
  @IsNumber()
  private readonly thresholdValue: number;

  private constructor(props: ThresholdProps) {
    super(props);
    this.thresholdValue = props.value;
    this.validate();
  }

  public static create(val: number): ThresholdVO {
    return new ThresholdVO({ value: val });
  }

  get value(): number {
    return this.props.value;
  }
}
