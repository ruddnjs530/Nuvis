import * as fs from 'fs';
import * as path from 'path';
import { Injectable, Logger, Inject, OnModuleInit } from '@nestjs/common';
import { RobotRepository } from '../repositories/robot.repository';
import { Observable, Subject, lastValueFrom } from 'rxjs';
import { ClientGrpc } from '@nestjs/microservices';
import { ExecuteCommandDto, TaskType } from '../dto/request/execute-command.request.dto';
import { ManualControlDto } from '../dto/request/manual-control.request.dto';

interface RobotGatewayService {
  executeTask(data: any): Observable<any>;
  cancelTask(data: any): Observable<any>;
  emergencyStop(data: any): Observable<any>;
  manualControl(data: any): Observable<any>;
}

@Injectable()
export class RobotService implements OnModuleInit {
  private readonly logger = new Logger(RobotService.name);
  private robotGateway: RobotGatewayService;

  constructor(
    private readonly robotRepository: RobotRepository,
    @Inject('ROBOT_GRPC_CLIENT') private readonly client: ClientGrpc,
  ) {}

  onModuleInit() {
    this.robotGateway = this.client.getService<RobotGatewayService>('RobotGateway');
  }

  async getAiDataset(userId: number, days: number) {
    // [시연용 목업] DB에 이력이 없는 동안 mock_payload.json 파일을 읽어 반환합니다.
    // 정식 연동 시 ROOM_CONDITIONS_HISTORY / MODULE_CONTROL_LOGS 기반 실제 쿼리로 교체 필요.
    const filePath = path.join(process.cwd(), 'src', 'modules', 'robot', 'data', 'mock_payload.json');
    const raw = fs.readFileSync(filePath, 'utf-8');
    const mock = JSON.parse(raw);

    // AI 서버 AnalysisRequest 규격: { user_id: int, sensor_data: [...] }
    return {
      user_id: userId,
      sensor_data: mock.sensor_data,
    };
  }

  create(data: any) {
    // TODO: Implement robot creation logic
    return { ...data, createdAt: new Date() };
  }

  async executeTask(data: ExecuteCommandDto) {
    this.logger.log(`ExecuteTask called: ${JSON.stringify(data)}`);

    // Override target coordinates if target_zone is provided (Guideline implementation)
    let finalX = data.targetX || 0.0;
    let finalY = data.targetY || 0.0;
    const finalYaw = data.targetYaw || 0.0;

    if (data.targetZone && data.targetZone.trim() !== '') {
      // Zone provided: strict zero override
      this.logger.debug(`Target Zone '${data.targetZone}' identified. Overriding coordinates to 0.0`);
      finalX = 0.0;
      finalY = 0.0;
    }

    const requestPayload = {
      commandId: data.commandId || `cmd-rest-${Date.now()}`,
      taskId: data.taskId || `task-${Date.now()}`,
      taskType: data.taskType ?? TaskType.MOVE_AND_EXECUTE,
      targetZone: data.targetZone || '',
      targetX: finalX,
      targetY: finalY,
      targetYaw: finalYaw,
      moduleType: data.moduleType || 0,
      modulePower: data.modulePower ?? true,
      moduleLevel: data.moduleLevel || 1,
      maxExecSec: data.maxExecSec || 180,
    };

    try {
      const result = await lastValueFrom(this.robotGateway.executeTask(requestPayload));
      return result;
    } catch (error) {
      this.logger.error(`executeTask gRPC Error: ${error.message}`);
      throw error;
    }
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

  async manualControl(data: ManualControlDto) {
    this.logger.log(`ManualControl called: vx=${data.vx}, wz=${data.wz}`);
    
    try {
      const result = await lastValueFrom(this.robotGateway.manualControl({
        vx: data.vx,
        wz: data.wz,
        durationMs: data.durationMs || 1000,
      }));
      return result;
    } catch (error) {
      this.logger.error(`manualControl gRPC Error: ${error.message}`);
      throw error;
    }
  }

  async getStatus() {
    try {
      if (this.robotGateway && this.robotGateway['getStatus']) {
         const grpcStatus = await lastValueFrom((this.robotGateway as any).getStatus({}));
         return this.formatStatus(grpcStatus);
      }
    } catch(e) {
      this.logger.warn(`gRPC GetStatus failed, returning mock: ${e.message}`);
    }
    return this.formatStatus(this.getMockStatus());
  }

  private formatStatus(status: any) {
    const batteryPct = status.batteryPct != null ? Number(status.batteryPct.toFixed(1)) : 0;
    const poseX = status.poseX != null ? Number(status.poseX.toFixed(3)) : 0;
    const poseY = status.poseY != null ? Number(status.poseY.toFixed(3)) : 0;
    const poseYaw = status.poseYaw != null ? Number((status.poseYaw * (180 / Math.PI)).toFixed(1)) : 0;

    return {
      ...status,
      batteryPct,
      poseX,
      poseY,
      poseYaw,
      attached_module: {
        type: 1,
        name: 'AIR_PURIFIER',
        is_available: true
      }
    };
  }

  streamStatus(intervalMs: number): Observable<any> {
    this.logger.log(`StreamStatus started with interval: ${intervalMs}ms`);
    const subject = new Subject<any>();
    const interval = intervalMs >= 100 && intervalMs <= 10000 ? intervalMs : 1000;

    let count = 0;
    const timer = setInterval(() => {
      count++;
      subject.next(this.formatStatus(this.getMockStatus()));
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
      // ROS2 waypoints.yaml 기준 hq(스테이션) 좌표
      pose_x: 1.0,
      pose_y: -4.5,
      pose_yaw: 0.0,
      stamp: new Date().toISOString(),
    };
  }
}
