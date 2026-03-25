import { Module } from '@nestjs/common';
import { ScheduleModule as NestScheduleModule } from '@nestjs/schedule';
import { EventModule } from './modules/event/event.module';
import { RobotModule } from './modules/robot/robot.module';
import { RoomModule } from './modules/room/room.module';
import { ScheduleModule } from './modules/schedule/schedule.module';
import { AuthModule } from './modules/auth/auth.module';
import { WebrtcModule } from './modules/webrtc/webrtc.module';

@Module({
  imports: [
    AuthModule,
    EventModule,
    RobotModule,
    RoomModule,
    NestScheduleModule.forRoot(),
    ScheduleModule,
    WebrtcModule,
  ],
  controllers: [],
  providers: [],
})
export class AppModule {}
