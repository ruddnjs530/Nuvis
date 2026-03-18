import { Module } from '@nestjs/common';
import { RobotController } from './robot.controller';
import { RegisterRobotUseCase } from '../../../application/robot/usecases/register-robot.usecase';
import { PrismaModule } from '../../../infrastructure/database/prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [RobotController],
  providers: [RegisterRobotUseCase],
  exports: [RegisterRobotUseCase],
})
export class RobotApiModule {}
