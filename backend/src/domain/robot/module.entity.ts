import { BaseEntity } from '../common/base.entity';
import { StatusVO } from './vo/status.vo';

export interface ModuleProps {
  type: string;
  status: StatusVO;
}

export class ModuleEntity extends BaseEntity<number> {
  private props: ModuleProps;

  private constructor(id: number, props: ModuleProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: ModuleProps): ModuleEntity {
    if (!props.type || props.type.trim().length === 0) {
      throw new Error("Module type cannot be empty");
    }
    return new ModuleEntity(id || 0, props);
  }

  get type(): string { return this.props.type; }
  get status(): StatusVO { return this.props.status; }

  public updateStatus(status: StatusVO): void {
    this.props.status = status;
  }
}
