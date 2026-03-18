import { IsNumber, Min, Max } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface HumidityProps {
  value: number;
}

export class HumidityVO extends ValueObject<HumidityProps> {
  @IsNumber()
  @Min(0, { message: 'Humidity cannot be negative' })
  @Max(100, { message: 'Humidity cannot exceed 100%' })
  private readonly humValue: number;

  private constructor(props: HumidityProps) {
    super(props);
    this.humValue = props.value;
    this.validate();
  }

  public static create(humidity: number): HumidityVO {
    return new HumidityVO({ value: humidity });
  }

  get value(): number {
    return this.props.value;
  }
}
