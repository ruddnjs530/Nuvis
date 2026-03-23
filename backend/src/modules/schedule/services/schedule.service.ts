import { Injectable } from '@nestjs/common';
import { ScheduleRepository } from '../repositories/schedule.repository';
import { RobotService } from '../../robot/services/robot.service';

@Injectable()
export class ScheduleService {
  constructor(
    private readonly scheduleRepository: ScheduleRepository,
    private readonly robotService: RobotService,
  ) {}

  create(data: any) {
    return { ...data, id: Date.now() };
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
