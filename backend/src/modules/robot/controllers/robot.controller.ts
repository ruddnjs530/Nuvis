import { Controller, Get, Post, Param, Body, UseGuards, Req } from '@nestjs/common';
import { ApiOperation, ApiResponse, ApiTags, ApiBearerAuth, ApiBody } from '@nestjs/swagger';
import { RobotService } from '../services/robot.service';
import { RankGuard } from 'src/common/guard/auth.guard';
import { GetUser } from 'src/common/decorator/get-user.decorator';
import { User } from 'src/modules/auth/models/user.model';
import { ExecuteCommandDto, ManualControlDto } from '../dto/robot.dto';

@ApiTags('Robot')
@ApiBearerAuth()
@Controller('api/robot')
export class RobotController {
  constructor(private readonly robotService: RobotService) {}

  @Get('dataset')
  @UseGuards(RankGuard)
  async previewDataset(@GetUser() user: User) {
    return this.robotService.getAiDataset(user.userId, 14);
  }

  // API requested by AI Team to pull dataset for a specific user
  @Get('dataset/:userId')
  @ApiOperation({ summary: 'AI 추천용 데이터셋 조회', description: '특정 사용자의 방별 환경 변화 및 제어 로그를 AI 학습/검증용 데이터로 제공합니다.' })
  async getAiDatasetForAiTeam(@Param('userId') userId: string) {
    return this.robotService.getAiDataset(Number(userId), 14);
  }

  @Post('command')
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '로봇 목표 태스크 (Command) 전송', description: '웨이포인트(Zone)나 x/y 좌표로 로봇을 이동시키고 모듈을 제어합니다. (gRPC 게이트웨이 연동)' })
  @ApiBody({ type: ExecuteCommandDto })
  async executeCommand(@Body() dto: ExecuteCommandDto) {
    return this.robotService.executeTask(dto);
  }

  @Post('manual-control')
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '로봇 수동 제어', description: '선속도와 각속도를 지정하여 로봇을 특정 시간 동안 수동 조작합니다.' })
  @ApiBody({ type: ManualControlDto })
  async manualControl(@Body() dto: ManualControlDto) {
    return this.robotService.manualControl(dto);
  }
}
