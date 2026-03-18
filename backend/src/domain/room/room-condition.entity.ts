import { BaseEntity } from '../common/base.entity';
import { TemperatureVO } from './vo/temperature.vo';
import { HumidityVO } from './vo/humidity.vo';
import { FineDustVO } from './vo/fine-dust.vo';

export interface RoomConditionProps {
  roomId: number;
  temperature: TemperatureVO;
  humidity: HumidityVO;
  fineDust: FineDustVO;
  updatedAt: Date;
}

export class RoomCondition extends BaseEntity<number> {
  private props: RoomConditionProps;

  private constructor(id: number, props: RoomConditionProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: RoomConditionProps): RoomCondition {
    return new RoomCondition(id || 0, props);
  }

  get roomId(): number { return this.props.roomId; }
  get temperature(): TemperatureVO { return this.props.temperature; }
  get humidity(): HumidityVO { return this.props.humidity; }
  get fineDust(): FineDustVO { return this.props.fineDust; }
  get updatedAt(): Date { return this.props.updatedAt; }

  public updateCondition(temp: TemperatureVO, hum: HumidityVO, dust: FineDustVO): void {
    this.props.temperature = temp;
    this.props.humidity = hum;
    this.props.fineDust = dust;
    this.props.updatedAt = new Date();
  }
}
