import { IsOptional } from 'class-validator';
import { ValueObject } from '../../common/value-object';

export interface MapDataProps {
  value: any | null;
}

export class MapDataVO extends ValueObject<MapDataProps> {
  @IsOptional()
  private readonly mapValue: any | null;

  private constructor(props: MapDataProps) {
    super(props);
    this.mapValue = props.value;
    this.validate();
  }

  public static create(mapData: any | null): MapDataVO {
    return new MapDataVO({ value: mapData });
  }

  get value(): any | null {
    return this.props.value;
  }
}
