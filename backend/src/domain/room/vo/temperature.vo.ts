import { IsNumber, Min, Max } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface TemperatureProps {
  value: number;
}

export class TemperatureVO extends ValueObject<TemperatureProps> {
  @IsNumber()
  @Min(-20, { message: 'Temperature cannot be below -20' })
  @Max(50, { message: 'Temperature cannot be above 50' })
  private readonly tempValue: number;

  private constructor(props: TemperatureProps) {
    super(props);
    this.tempValue = props.value;
    this.validate();
  }

  public static create(temp: number): TemperatureVO {
    return new TemperatureVO({ value: temp });
  }

  get value(): number {
    return this.props.value;
  }
}
