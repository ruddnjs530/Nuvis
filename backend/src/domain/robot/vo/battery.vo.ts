import { IsNumber, Min, Max } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface BatteryProps {
  value: number;
}

export class BatteryVO extends ValueObject<BatteryProps> {
  @IsNumber()
  @Min(0, { message: 'Battery level cannot be less than 0' })
  @Max(100, { message: 'Battery level cannot exceed 100' })
  private readonly batteryValue: number;

  private constructor(props: BatteryProps) {
    super(props);
    this.batteryValue = props.value;
    this.validate();
  }

  public static create(level: number): BatteryVO {
    return new BatteryVO({ value: level });
  }

  get value(): number {
    return this.props.value;
  }
}
