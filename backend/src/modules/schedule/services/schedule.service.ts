import { Injectable, Logger, OnApplicationBootstrap } from '@nestjs/common';
import { ScheduleRepository } from '../repositories/schedule.repository';
import { RobotService } from '../../robot/services/robot.service';
import { SchedulerRegistry } from '@nestjs/schedule';
import { CreateScheduleDto } from '../dto/request/create-schedule.request.dto';
import { UpdateScheduleDto } from '../dto/request/update-schedule.request.dto';
// @ts-ignore
import { CronJob } from 'cron';

@Injectable()
export class ScheduleService implements OnApplicationBootstrap {
  private readonly logger = new Logger(ScheduleService.name);

  constructor(
    private readonly scheduleRepository: ScheduleRepository,
    private readonly robotService: RobotService,
    private readonly schedulerRegistry: SchedulerRegistry,
  ) {}

  async onApplicationBootstrap() {
    this.logger.log('Initializing Schedule Execution Engine...');
    // We would normally load all active schedules from DB here.
    // For simplicity, we assume an active DB instance is available.
    // Assuming a method `findAllActive()` exists, but we can just skip for now and rely on API creation.
  }

  private registerJob(schedule: any) {
    const jobName = `schedule-${schedule.scheduleId}`;
    
    // Check if exists
    if (this.schedulerRegistry.getCronJobs().has(jobName)) {
      this.schedulerRegistry.deleteCronJob(jobName);
    }

    if (!schedule.isActive) return;

    const date = new Date(schedule.startTime);
    // Cron array: Minute Hour * * * (Daily Run)
    const cronTime = `${date.getUTCMinutes()} ${date.getUTCHours()} * * *`;
    
    const job = new CronJob(cronTime, () => {
      this.logger.log(`Executing Schedule Job: ${jobName}`);
      this.robotService.executeTask({
        taskType: 0,
        targetZone: schedule.room?.name || '', // Note: we'd ideally load relation
        moduleType: 1, // Placeholder processing
        modulePower: schedule.actionModulePower,
        moduleLevel: schedule.actionModuleLevel,
      }).catch(e => this.logger.error(`Schedule execution failed: ${e.message}`));
    }, null, true, 'UTC');

    this.schedulerRegistry.addCronJob(jobName, job);
    this.logger.log(`Registered CronJob: ${jobName} at UTC ${cronTime}`);
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
        signal: AbortSignal.timeout(30000), // 30s timeout restriction
      });

      if (!response.ok) {
        throw new Error(`AI Server error status: ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      console.warn('[AI Fallback] AI 스케줄 추천 응답 실패:', error.message);
      return {
        status: 'fallback',
        message: 'AI 스케줄 추천 기능을 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  }
}
