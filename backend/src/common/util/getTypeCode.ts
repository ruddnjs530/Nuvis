import { NotFoundException } from '@nestjs/common';
import { ChartTypeCode } from '../lib/chart-type-code';

export function getTypeCode(type: string): number {
  switch (type) {
    case 'novice':
      return ChartTypeCode.novice;
    case 'advanced':
      return ChartTypeCode.advanced;
    case 'exhaust':
      return ChartTypeCode.exhaust;
    case 'maximum':
      return ChartTypeCode.maximum;
    case 'infinite':
      return ChartTypeCode.infinite;
    case 'gravity':
      return ChartTypeCode.gravity;
    case 'heavenly':
      return ChartTypeCode.heavenly;
    case 'vivid':
      return ChartTypeCode.vivid;
    case 'exceed':
      return ChartTypeCode.exceed;
    case 'ultimate':
      return ChartTypeCode.ultimate;
    default:
      throw new NotFoundException(`Unknown chart type: ${type}`);
  }
}
