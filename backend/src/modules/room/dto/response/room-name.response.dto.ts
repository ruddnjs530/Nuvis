export class RoomNameResponseDto {
  roomId: number;
  name: string;
}

export class RoomNameListResponseDto {
  data: RoomNameResponseDto[];
}
