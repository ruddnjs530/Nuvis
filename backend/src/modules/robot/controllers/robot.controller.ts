import { Controller, Get, Param, UseGuards, Req } from '@nestjs/common';
import { RobotService } from '../services/robot.service';
import { RankGuard } from 'src/common/guard/auth.guard';
import { GetUser } from 'src/common/decorator/get-user.decorator';
import { User } from 'src/modules/auth/models/user.model';

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
  async getAiDatasetForAiTeam(@Param('userId') userId: string) {
    return this.robotService.getAiDataset(Number(userId), 14);
  }
}
