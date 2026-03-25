import { Module } from '@nestjs/common';
import { ClientsModule, Transport } from '@nestjs/microservices';
import { join } from 'path';
import { RobotController } from './controllers/robot.controller';
import { RobotGrpcController } from './controllers/robot.grpc.controller';
import { RobotService } from './services/robot.service';
import { RobotRepository } from './repositories/robot.repository';
import { RobotGateway } from './gateways/robot.gateway';

@Module({
  imports: [
    ClientsModule.register([
      {
        name: 'ROBOT_GRPC_CLIENT',
        transport: Transport.GRPC,
        options: {
          package: 'robot.gateway.v1',
          protoPath: join(process.cwd(), 'proto/robot.proto'),
          url: process.env.ROBOT_GRPC_URL || 'localhost:50051',
        },
      },
    ]),
  ],
  controllers: [RobotController, RobotGrpcController],
  providers: [RobotService, RobotRepository, RobotGateway],
  exports: [RobotService],
})
export class RobotModule {}
