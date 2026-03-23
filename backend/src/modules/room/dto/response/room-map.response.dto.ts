export class RoomMapDto {
  width: number;
  height: number;
  resolution: number;
  origin: { x: number; y: number; theta: number };
  mapImageUrl: string;
}

export class RoomMapResponseDto {
  roomId: number;
  name: string;
  mapData: RoomMapDto | null;
}

export class RoomMapListResponseDto {
  data: RoomMapResponseDto[];
}
