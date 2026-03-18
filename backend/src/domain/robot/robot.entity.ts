import { BaseEntity } from '../common/base.entity';
import { BatteryVO } from './vo/battery.vo';
import { StatusVO } from './vo/status.vo';

export interface RobotProps {
  userId: number;
  status: StatusVO;
  batteryLevel: BatteryVO;
  currentRoomId: number | null;
  currentModuleId: number | null;
}

export class Robot extends BaseEntity<number> {
  private props: RobotProps;

  private constructor(id: number, props: RobotProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: RobotProps): Robot {
    return new Robot(id || 0, props);
  }

  get userId(): number { return this.props.userId; }
  get status(): StatusVO { return this.props.status; }
  get batteryLevel(): BatteryVO { return this.props.batteryLevel; }
  get currentRoomId(): number | null { return this.props.currentRoomId; }
  get currentModuleId(): number | null { return this.props.currentModuleId; }

  public updateStatus(status: StatusVO): void {
    this.props.status = status;
  }

  public updateBattery(level: BatteryVO): void {
    this.props.batteryLevel = level;
  }

  public moveToRoom(roomId: number): void {
    this.props.currentRoomId = roomId;
  }

  public attachModule(moduleId: number): void {
    this.props.currentModuleId = moduleId;
  }

  public detachModule(): void {
    this.props.currentModuleId = null;
  }
}
