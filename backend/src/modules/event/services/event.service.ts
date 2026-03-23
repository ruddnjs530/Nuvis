import { Injectable } from '@nestjs/common';
import { EventRepository } from '../repositories/event.repository';
import { RobotService } from '../../robot/services/robot.service';

@Injectable()
export class EventService {
  constructor(
    private readonly eventRepository: EventRepository,
    private readonly robotService: RobotService,
  ) {}

  create(data: any) {
    return { ...data, id: Date.now() };
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

      return await response.json();
    } catch (error: any) {
      console.warn('[AI Fallback] AI 서버 응답 실패:', error.message);
      return {
        status: 'fallback',
        message: 'AI 추천 기능을 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.',
      };
    }
  }
}
