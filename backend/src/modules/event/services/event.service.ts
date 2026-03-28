import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { EventRepository } from '../repositories/event.repository';
import { RobotService } from '../../robot/services/robot.service';
import { RoomService } from '../../room/services/room.service';
import { keysToCamel } from 'src/common/utils/case.util';
import { TaskType } from '../../robot/dto/robot.dto';

@Injectable()
export class EventService {
  private readonly logger = new Logger(EventService.name);
  private lastTriggered = new Map<number, number>(); // eventId -> timestamp

  constructor(
    private readonly eventRepository: EventRepository,
    private readonly robotService: RobotService,
    private readonly roomService: RoomService,
  ) {}

  @Cron(CronExpression.EVERY_10_SECONDS)
  async handleEventAutomation() {
    try {
      // 1. 활성화된(isActive) 모든 자동화 규칙 가져오기
      const activeEvents = await this.eventRepository.findActiveEvents();
      if (!activeEvents.length) return;

      const userIds = [...new Set(activeEvents.map(e => e.userId))];

      for (const userId of userIds) {
        // 2. 현재 방 번호와 센서 상태 조회 (RoomService의 인메모리 Mock 활용)
        const roomDataResult = await this.roomService.getRoomData(userId);
        const roomsData = roomDataResult.data;

        const userEvents = activeEvents.filter(e => e.userId === userId);
        for (const event of userEvents) {
          // 중복 스팸 방지 (5분 쿨타임)
          const lastTime = this.lastTriggered.get(event.eventId) || 0;
          if (Date.now() - lastTime < 5 * 60 * 1000) {
            continue;
          }

          const room = roomsData.find(r => r.roomId === event.roomId);
          if (!room || !room.condition) continue;

          const conditionVal = this.getConditionValue(room.condition, event.conditionType);
          if (conditionVal === null) continue;

          // 3. 조건 검사
          const isMet = this.evaluateCondition(conditionVal, event.conditionOperator, event.thresholdValue);
          
          if (isMet) {
            this.logger.log(`[Event Automation] Event #${event.eventId} triggered! Room: ${room.name}, Target Module: ${event.actionModuleType}`);
            // 실행 기록 (쿨타임 반영)
            this.lastTriggered.set(event.eventId, Date.now());

            // 4. 로봇에 실제 제어 명령(Command) 전송
            try {
              await this.robotService.executeTask({
                commandId: `evt-${event.eventId}-${Date.now()}`,
                taskId: `task-evt-${event.eventId}-${Date.now()}`,
                taskType: TaskType.MOVE_AND_EXECUTE,
                targetZone: (room as any).targetZone || '',
                moduleType: this.getModuleTypeId(event.actionModuleType),
                modulePower: event.actionModulePower ?? true,
                moduleLevel: event.actionModuleLevel ?? 1,
              });
              
              // 모듈 가동 성공 시 방의 센서 수치에 즉각 반영 (시뮬레이터 효과)
              if (event.actionModulePower !== false) {
                await this.roomService.applyDemoAction(event.roomId, event.actionModuleType.toLowerCase());
              }

              this.logger.log(`[Event Automation] Robot command sent successfully.`);
            } catch (e) {
              this.logger.error(`[Event Automation] Failed to start robot task: ${e.message}`);
            }
          }
        }
      }
    } catch (e) {
      this.logger.error(`[Event Automation] Error running task: ${e.message}`);
    }
  }

  private getConditionValue(condition: any, type: string): number | null {
    switch(type) {
      case 'TEMP': return condition.temperature;
      case 'HUMIDITY': return condition.humidity;
      case 'FINE_DUST': return condition.fineDust;
      default: return null;
    }
  }

  private evaluateCondition(val: number, op: string, threshold: number): boolean {
    switch(op) {
      case 'GT': return val > threshold;
      case 'LT': return val < threshold;
      case 'EQ': return val === threshold;
      default: return false;
    }
  }

  private getModuleTypeId(name: string): number {
    switch(name) {
      case 'AIR_PURIFIER': return 1;
      case 'HUMIDIFIER': return 2;
      case 'DEHUMIDIFIER': return 3;
      default: return 0;
    }
  }

  async findAll(userId: number) {
    return this.eventRepository.findAll(userId);
  }

  async create(userId: number, createEventDto: any) {
    return this.eventRepository.create(userId, createEventDto);
  }

  async update(eventId: number, userId: number, updateEventDto: any) {
    return this.eventRepository.update(eventId, userId, updateEventDto);
  }

  async remove(eventId: number, userId: number) {
    return this.eventRepository.delete(eventId, userId);
  }

  async getEventSuggestions(userId: number) {
    try {
      const payload = await this.robotService.getAiDataset(userId, 14);
      const url = `${process.env.AI_RECOMMENDATION_BASE_URL || 'http://localhost:9000'}/api/event/ai-suggestions`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000), // 30s timeout restriction
      });

      if (!response.ok) {
        throw new Error(`AI Server error status: ${response.status}`);
      }

      return keysToCamel(await response.json());
    } catch (error: any) {
      console.warn('[AI Fallback] AI 서버 응답 실패:', error.message);
      return {
        status: 'fallback',
        message: 'AI 추천 기능을 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  }
}
