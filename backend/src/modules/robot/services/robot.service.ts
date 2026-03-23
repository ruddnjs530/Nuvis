import { Injectable, Logger } from '@nestjs/common';
import { RobotRepository } from '../repositories/robot.repository';
import { Observable, Subject } from 'rxjs';

@Injectable()
export class RobotService {
  private readonly logger = new Logger(RobotService.name);

  constructor(private readonly robotRepository: RobotRepository) {}

  async getAiDataset(userId: number, days: number) {
    return { userId, days, data: [] };
  }

  create(data: any) {
    // TODO: Implement robot creation logic
    return { ...data, createdAt: new Date() };
  }

  executeTask(data: any) {
    this.logger.log(`ExecuteTask called: ${JSON.stringify(data)}`);
    return {
      accepted: true,
      task_id: data.task_id || 'task-1234',
      final_state: 0, // FINAL_COMPLETED
      result_code: 0,
      result_message: 'Task completed successfully (Placeholder)',
      error_code: 0,
    };
  }

  cancelTask(data: any) {
    this.logger.log(`CancelTask called: ${JSON.stringify(data)}`);
    return {
      accepted: true,
      state: 2, // FINAL_CANCELED
      message: 'Task cancelled safely',
    };
  }

  emergencyStop(data: any) {
    this.logger.warn(`EMERGENCY STOP CALLED! Reason: ${data.reason}`);
    return {
      accepted: true,
      applied_at: new Date().toISOString(),
      message: 'Emergency stop activated',
    };
  }

  manualControl(data: any) {
    this.logger.log(`ManualControl called: vx=${data.vx}, wz=${data.wz}`);
    return {
      accepted: true,
      message: 'Manual control command sent',
    };
  }

  getStatus() {
    return this.getMockStatus();
  }

  streamStatus(intervalMs: number): Observable<any> {
    this.logger.log(`StreamStatus started with interval: ${intervalMs}ms`);
    const subject = new Subject<any>();
    const interval = intervalMs >= 100 && intervalMs <= 10000 ? intervalMs : 1000;

    let count = 0;
    const timer = setInterval(() => {
      count++;
      subject.next(this.getMockStatus());
      if (count >= 10) {
        clearInterval(timer);
        subject.complete();
      }
    }, interval);

    return subject.asObservable();
  }

  private getMockStatus() {
    return {
      robot_id: 'robot-R1',
      mode: 0, // IDLE
      task_state: 0,
      active_task_id: '',
      battery_pct: 85.5,
      is_charging: false,
      safety_state: 0, // NORMAL
      last_error_code: 0,
      pose_x: 10.5,
      pose_y: 20.3,
      pose_yaw: 1.57,
      stamp: new Date().toISOString(),
    };
  }
}
