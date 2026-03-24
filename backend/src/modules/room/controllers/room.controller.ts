import { Controller, Get, Post, Param, Body, UseGuards } from '@nestjs/common';
import { ApiOperation, ApiResponse, ApiTags, ApiBearerAuth } from '@nestjs/swagger';
import { RoomService } from '../services/room.service';
import { RoomNameListResponseDto } from '../dto/response/room-name.response.dto';
import { RoomDataListResponseDto } from '../dto/response/room-data.response.dto';
import { RoomMapListResponseDto } from '../dto/response/room-map.response.dto';
import { RankGuard } from 'src/common/guard/auth.guard';
import { GetUser } from 'src/common/decorator/get-user.decorator';
import { User } from 'src/modules/auth/models/user.model';

@ApiTags('Room')
@ApiBearerAuth()
@Controller('api/room')
export class RoomController {
  constructor(private readonly roomService: RoomService) {}

  @Get('name')
  @UseGuards(RankGuard)
  async getAllRoomNames(@GetUser() user: User): Promise<RoomNameListResponseDto> {
    return this.roomService.getAllRoomNames(user.userId);
  }

  @Get('data')
  @UseGuards(RankGuard)
  async getRoomData(@GetUser() user: User): Promise<RoomDataListResponseDto> {
    return this.roomService.getRoomData(user.userId);
  }

  @Get('map')
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '방별 지도 및 구역 데이터 조회', description: '생성된 모든 방의 지도 메타데이터와 폴리곤(경계선) 데이터를 조회합니다.' })
  @ApiResponse({ status: 200, description: '성공적으로 맵 데이터를 반환합니다.', type: RoomMapListResponseDto })
  async getRoomMaps(@GetUser() user: User): Promise<RoomMapListResponseDto> {
    return this.roomService.getRoomMaps(user.userId);
  }

  // 데모 시연용: 특정 방에 가습기/청정기 등을 켰다고 시뮬레이션
  @Post(':roomId/demo-action')
  @UseGuards(RankGuard)
  async applyDemoAction(
    @Param('roomId') roomId: string,
    @Body('actionType') actionType: string,
  ) {
    return this.roomService.applyDemoAction(Number(roomId), actionType);
  }
}
