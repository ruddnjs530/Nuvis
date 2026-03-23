export class CreateRoomDto {}

export class RoomNameResponseDto {
  roomId: number;
  name: string;
}

export class RoomNameListResponseDto {
  data: RoomNameResponseDto[];
}

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
