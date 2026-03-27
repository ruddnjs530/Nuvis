import { Injectable, Logger, OnApplicationBootstrap } from '@nestjs/common';
import { ScheduleRepository } from '../repositories/schedule.repository';
import { RobotService } from '../../robot/services/robot.service';
import { SchedulerRegistry } from '@nestjs/schedule';
import { CreateScheduleDto } from '../dto/request/create-schedule.request.dto';
import { UpdateScheduleDto } from '../dto/request/update-schedule.request.dto';
import { keysToCamel } from 'src/common/utils/case.util';
// @ts-ignore
import { CronJob } from 'cron';

/**
 * actionModuleType(문자열) → gRPC module_type(정수) 매핑
 * proto에서 module_type은 int32이며 ROS2 측과 합의된 값입니다.
 */
const MODULE_TYPE_MAP: Record<string, number> = {
  AIR_PURIFIER:  1,
  HUMIDIFIER:    2,
  DEHUMIDIFIER:  3,
};

function toModuleType(actionModuleType: string): number {
  return MODULE_TYPE_MAP[actionModuleType?.toUpperCase()] ?? 0;
}

@Injectable()
export class ScheduleService implements OnApplicationBootstrap {
  private readonly logger = new Logger(ScheduleService.name);

  constructor(
    private readonly scheduleRepository: ScheduleRepository,
    private readonly robotService: RobotService,
    private readonly schedulerRegistry: SchedulerRegistry,
  ) {}

  /** ① 서버 재시작 시 DB의 isActive 스케줄을 전부 CronJob으로 복원 */
  async onApplicationBootstrap() {
    this.logger.log('Initializing Schedule Execution Engine...');
    const activeSchedules = await this.scheduleRepository.findAllActive();
    for (const schedule of activeSchedules) {
      this.registerJob(schedule);
    }
    this.logger.log(`Restored ${activeSchedules.length} active schedule(s).`);
  }

  private registerJob(schedule: any) {
    const jobName = `schedule-${schedule.scheduleId}`;

    // 기존 job 제거
    if (this.schedulerRegistry.getCronJobs().has(jobName)) {
      this.schedulerRegistry.deleteCronJob(jobName);
    }

    if (!schedule.isActive) return;

    /**
     * ② KST(Asia/Seoul) 기준 크론식 생성
     * startTime은 DB에 Time 타입으로 저장 → 오늘 날짜 기준 Date 객체로 파싱
     * 'Asia/Seoul' 타임존을 CronJob에 직접 전달
     */
    const date = new Date(schedule.startTime);
    // CronJob의 timezone을 'Asia/Seoul'로 지정하면
    // 크론식의 시·분이 KST 기준으로 해석됩니다.
    // DB의 Time 값을 UTC로 읽은 숫자 그대로 사용하면
    // "사용자가 입력한 시각"에 맞춰 KST로 실행됩니다.
    const cronTime = `${date.getUTCMinutes()} ${date.getUTCHours()} * * *`;

    const job = new CronJob(
      cronTime,
      () => {
        this.logger.log(`Executing Schedule Job: ${jobName}`);

        /**
         * ③ gRPC payload — room.targetZone + 실제 moduleType 매핑
         * repository에서 room relation을 include하므로 schedule.room.targetZone 접근 가능
         */
        const targetZone = schedule.room?.targetZone ?? '';
        const moduleType = toModuleType(schedule.actionModuleType);

        this.robotService
          .executeTask({
            taskType: 0,           // TASK_MOVE_AND_EXECUTE
            targetZone,            // room.targetZone (ex: 'living_room')
            moduleType,            // AIR_PURIFIER=1, HUMIDIFIER=2, DEHUMIDIFIER=3
            modulePower: schedule.actionModulePower,
            moduleLevel: schedule.actionModuleLevel,
          })
          .catch((e) =>
            this.logger.error(`Schedule execution failed: ${e.message}`),
          );
      },
      null,
      true,
      'Asia/Seoul', // ① CronJob 타임존을 KST로 고정
    );

    this.schedulerRegistry.addCronJob(jobName, job);
    this.logger.log(
      `Registered CronJob: ${jobName} at KST ${cronTime} (zone: Asia/Seoul)`,
    );
  }

  async findAllByUserId(userId: number) {
    return this.scheduleRepository.findAllByUserId(userId);
  }

  async create(userId: number, dto: CreateScheduleDto) {
    const schedule = await this.scheduleRepository.create(userId, dto);
    this.registerJob(schedule);
    return schedule;
  }

  async update(scheduleId: number, dto: UpdateScheduleDto) {
    const schedule = await this.scheduleRepository.update(scheduleId, dto);
    this.registerJob(schedule);
    return schedule;
  }

  async delete(scheduleId: number) {
    const jobName = `schedule-${scheduleId}`;
    if (this.schedulerRegistry.getCronJobs().has(jobName)) {
      this.schedulerRegistry.deleteCronJob(jobName);
    }
    return this.scheduleRepository.delete(scheduleId);
  }

  async getScheduleSuggestions(userId: number) {
    try {
      const payload = await this.robotService.getAiDataset(userId, 14);
      const url = `${process.env.AI_RECOMMENDATION_BASE_URL || 'http://localhost:9000'}/api/schedule/ai-suggestions`;

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000),
      });

      if (!response.ok) {
        throw new Error(`AI Server error status: ${response.status}`);
      }

      return keysToCamel(await response.json());
    } catch (error: any) {
      console.warn('[AI Fallback] AI 스케줄 추천 응답 실패:', error.message);
      return {
        status: 'fallback',
        message: 'AI 스케줄 추천 기능을 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  }
}
