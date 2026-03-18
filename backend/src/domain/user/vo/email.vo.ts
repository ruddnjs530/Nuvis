import { IsEmail } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface EmailProps {
  value: string;
}

export class EmailVO extends ValueObject<EmailProps> {
  @IsEmail({}, { message: 'Invalid email format' })
  private readonly emailValue: string;

  private constructor(props: EmailProps) {
    super(props);
    this.emailValue = props.value;
    this.validate();
  }

  public static create(email: string): EmailVO {
    return new EmailVO({ value: email });
  }

  get value(): string {
    return this.props.value;
  }
}
