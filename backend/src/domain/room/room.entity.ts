import { BaseEntity } from '../common/base.entity';
import { MapDataVO } from './vo/map-data.vo';

export interface RoomProps {
  userId: number;
  name: string;
  mapData: MapDataVO | null;
}

export class Room extends BaseEntity<number> {
  private props: RoomProps;

  private constructor(id: number, props: RoomProps) {
    super(id);
    this.props = props;
  }

  public static create(id: number | null, props: RoomProps): Room {
    if (!props.name || props.name.trim().length === 0) {
      throw new Error("Room name cannot be empty");
    }
    return new Room(id || 0, props);
  }

  get userId(): number { return this.props.userId; }
  get name(): string { return this.props.name; }
  get mapData(): MapDataVO | null { return this.props.mapData; }

  public rename(name: string): void {
    if (!name || name.trim().length === 0) {
      throw new Error("Room name cannot be empty");
    }
    this.props.name = name;
  }

  public updateMapData(mapData: MapDataVO): void {
    this.props.mapData = mapData;
  }
}
