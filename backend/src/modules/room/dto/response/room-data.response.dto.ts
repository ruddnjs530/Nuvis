export class RoomConditionDto {
  temperature: number;
  humidity: number;
  fineDust: number;
  updatedAt: Date;
}

export class RoomDataResponseDto {
  roomId: number;
  name: string;
  condition: RoomConditionDto | null;
}

export class RoomDataListResponseDto {
  data: RoomDataResponseDto[];
}
