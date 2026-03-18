import { IsString, MinLength } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface PasswordHashProps {
  value: string;
}

export class PasswordHashVO extends ValueObject<PasswordHashProps> {
  @IsString()
  @MinLength(8, { message: 'Password hash must be at least 8 characters long' })
  private readonly hashValue: string;

  private constructor(props: PasswordHashProps) {
    super(props);
    this.hashValue = props.value;
    this.validate();
  }

  public static create(hash: string): PasswordHashVO {
    return new PasswordHashVO({ value: hash });
  }

  get value(): string {
    return this.props.value;
  }
}
