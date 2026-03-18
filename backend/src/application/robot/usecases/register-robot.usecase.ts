import { Injectable } from '@nestjs/common';
import { Robot, RobotProps } from '../../../domain/robot/robot.entity';
import { BatteryVO } from '../../../domain/robot/vo/battery.vo';
import { StatusVO } from '../../../domain/robot/vo/status.vo';
import { PrismaService } from '../../../infrastructure/database/prisma/prisma.service';

export interface RegisterRobotCommand {
  userId: number;
}

@Injectable()
export class RegisterRobotUseCase {
  constructor(private readonly prisma: PrismaService) {}

  async execute(command: RegisterRobotCommand): Promise<Robot> {
    const defaultBattery = BatteryVO.create(100);
    const initialStatus = StatusVO.create('IDLE');

    const robotProps: RobotProps = {
      userId: command.userId,
      status: initialStatus,
      batteryLevel: defaultBattery,
      currentRoomId: null,
      currentModuleId: null,
    };
    
    // Validate domain invariants
    const robot = Robot.create(null, robotProps);

    const savedRecord = await this.prisma.robot.create({
      data: {
        userId: robot.userId,
        status: robot.status.value,
        batteryLevel: robot.batteryLevel.value,
        currentRoomId: robot.currentRoomId,
        currentModuleId: robot.currentModuleId,
      },
    });

    return Robot.create(savedRecord.robotId, {
      userId: savedRecord.userId,
      status: StatusVO.create(savedRecord.status),
      batteryLevel: BatteryVO.create(savedRecord.batteryLevel),
      currentRoomId: savedRecord.currentRoomId,
      currentModuleId: savedRecord.currentModuleId,
    });
  }
}
