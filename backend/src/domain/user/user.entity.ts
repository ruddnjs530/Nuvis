import { BaseEntity } from '../common/base.entity';
import { EmailVO } from './vo/email.vo';
import { PasswordHashVO } from './vo/password-hash.vo';

export interface UserProps {
  email: EmailVO;
  passwordHash: PasswordHashVO;
  name: string;
  createdAt?: Date;
}

export class User extends BaseEntity<number> {
  private props: UserProps;

  private constructor(id: number, props: UserProps) {
    super(id);
    this.props = {
      ...props,
      createdAt: props.createdAt || new Date(),
    };
  }

  public static create(id: number | null, props: UserProps): User {
    if (!props.name || props.name.trim().length === 0) {
        throw new Error("User name cannot be empty");
    }
    // Set 0 as temporary ID for new entities, proper ID assigned by DB on save
    return new User(id || 0, props); 
  }

  get email(): EmailVO {
    return this.props.email;
  }

  get passwordHash(): PasswordHashVO {
    return this.props.passwordHash;
  }

  get name(): string {
    return this.props.name;
  }

  get createdAt(): Date {
    return this.props.createdAt!;
  }
  
  public changeName(newName: string): void {
      if (!newName || newName.trim().length === 0) {
          throw new Error("User name cannot be empty");
      }
      this.props.name = newName;
  }
  
  public changePassword(newHash: PasswordHashVO): void {
      this.props.passwordHash = newHash;
  }
}
