import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from './infrastructure/database/prisma/prisma.module';

// Domain API Modules
import { UserApiModule } from './presentation/api/user/user.module';
import { RoomApiModule } from './presentation/api/room/room.module';
import { RobotApiModule } from './presentation/api/robot/robot.module';
import { ScheduleApiModule } from './presentation/api/schedule/schedule.module';
import { EventApiModule } from './presentation/api/event/event.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    PrismaModule,
    
    // Feature Modules
    UserApiModule,
    RoomApiModule,
    RobotApiModule,
    ScheduleApiModule,
    EventApiModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
