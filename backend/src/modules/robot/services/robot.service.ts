import { Injectable, forwardRef, Inject } from '@nestjs/common';
import { RobotRepository } from '../repositories/robot.repository';
import { ModuleControlLogRepository } from '../repositories/module-control-log.repository';
import { RoomConditionHistoryRepository } from '../../room/repositories/room-condition-history.repository';

@Injectable()
export class RobotService {
  constructor(
    private readonly robotRepository: RobotRepository,
    private readonly moduleLogRepo: ModuleControlLogRepository,
    @Inject(forwardRef(() => RoomConditionHistoryRepository))
    private readonly roomConditionRepo: RoomConditionHistoryRepository,
  ) {}

  create(data: any) {
    // TODO: Implement robot creation logic
    return { ...data, createdAt: new Date() };
  }

  async getAiDataset(userId: number, days: number = 14) {
    const sensors = await this.roomConditionRepo.findRecentByUserId(userId, days);
    const logs = await this.moduleLogRepo.findRecentByUserId(userId, days);

    // AI Team requested format: joining 14 days of sensors with the latest device state
    const sensorData = sensors.map((sensor) => {
      // Find logs created before or exactly at the sensor's recorded time
      const recentLogs = logs.filter(log => log.createdAt <= sensor.recordedAt);
      
      const getLatestStatus = (type: string) => {
        const typeLogs = recentLogs.filter(l => l.actionModuleType === type);
        if (typeLogs.length === 0) return 0;
        const lastLog = typeLogs[typeLogs.length - 1];
        return lastLog.action === 'ON' ? 1 : 0;
      };

      return {
        timestamp: sensor.recordedAt.toISOString(),
        temperature: sensor.temperature,
        humidity: sensor.humidity,
        fine_dust: sensor.fineDust,
        air_purifier_on: getLatestStatus('air_purifier'),
        humidifier_on: getLatestStatus('humidifier'),
        dehumidifier_on: getLatestStatus('dehumidifier'),
      };
    });

    return {
      user_id: userId,
      sensor_data: sensorData,
    };
  }
}
