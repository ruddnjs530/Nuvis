import { IsString, IsNotEmpty } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface StatusProps {
  value: string;
}

export class StatusVO extends ValueObject<StatusProps> {
  @IsString()
  @IsNotEmpty({ message: 'Status cannot be empty' })
  private readonly statusValue: string;

  private constructor(props: StatusProps) {
    super(props);
    this.statusValue = props.value;
    this.validate();
  }

  public static create(status: string): StatusVO {
    return new StatusVO({ value: status });
  }

  get value(): string {
    return this.props.value;
  }
}
