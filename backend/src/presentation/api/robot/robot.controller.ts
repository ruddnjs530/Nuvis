import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { RegisterRobotUseCase } from '../../../application/robot/usecases/register-robot.usecase';
import { RegisterRobotDto } from './dto/register-robot.dto';

@Controller('robots')
export class RobotController {
  constructor(private readonly registerRobotUseCase: RegisterRobotUseCase) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async registerRobot(@Body() registerRobotDto: RegisterRobotDto) {
    const robot = await this.registerRobotUseCase.execute({
      userId: registerRobotDto.userId,
    });

    return {
      message: 'Robot registered successfully',
      data: {
        id: robot.id,
        userId: robot.userId,
        status: robot.status.value,
        batteryLevel: robot.batteryLevel.value,
      },
    };
  }
}
