import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CoordinateDto {
  @ApiProperty({ description: 'X 좌표', example: 1.5 })
  x: number;

  @ApiProperty({ description: 'Y 좌표', example: -2.3 })
  y: number;

  @ApiPropertyOptional({ description: '회전각 (Theta)', example: 0.0 })
  theta?: number;
}

export class RoomMapDataDto {
  @ApiProperty({ description: '맵 이미지 S3(또는 구글스토리지 등) URL', example: 'https://myserver/maps/house_map.png' })
  mapImageUrl: string;

  @ApiProperty({ description: 'Nav2 맵 해상도 (m/px)', example: 0.05 })
  resolution: number;

  @ApiProperty({ description: 'Nav2 맵 원점 (Origin)', type: CoordinateDto })
  origin: CoordinateDto;

  @ApiPropertyOptional({ description: '해당 방의 다각형 구역 경계선 좌표 리스트', type: [CoordinateDto] })
  boundaries?: CoordinateDto[];

  @ApiPropertyOptional({ description: '해당 방으로 로봇 이동 시 기준이 되는 목표 중심 좌표', type: CoordinateDto })
  centerPoint?: CoordinateDto;
}

export class RoomMapResponseDto {
  @ApiProperty({ description: '방 ID', example: 1 })
  roomId: number;

  @ApiProperty({ description: '방 이름', example: '거실' })
  name: string;

  @ApiPropertyOptional({ description: '맵 데이터 구조체', type: RoomMapDataDto })
  mapData: RoomMapDataDto | null;
}

export class RoomMapListResponseDto {
  @ApiProperty({ description: '방 지도 데이터 리스트', type: [RoomMapResponseDto] })
  data: RoomMapResponseDto[];
}
