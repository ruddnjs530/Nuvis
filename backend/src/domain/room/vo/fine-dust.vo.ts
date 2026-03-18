import { IsNumber, Min } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface FineDustProps {
  value: number;
}

export class FineDustVO extends ValueObject<FineDustProps> {
  @IsNumber()
  @Min(0, { message: 'Fine dust level cannot be negative' })
  private readonly dustValue: number;

  private constructor(props: FineDustProps) {
    super(props);
    this.dustValue = props.value;
    this.validate();
  }

  public static create(dust: number): FineDustVO {
    return new FineDustVO({ value: dust });
  }

  get value(): number {
    return this.props.value;
  }
}
