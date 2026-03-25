import { ChartBubble02Icon, DropletIcon } from '@hugeicons/core-free-icons';

import AppCard from '~/components/common/app-card';
import Icon from '~/components/common/icon';
import SectionHeader from '~/components/common/section-header';
import Spinner from '~/components/common/spinner';
import { cn } from '~/lib/utils';

import { useRoomDataQuery } from '../api/queries';

// ── Types ─────────────────────────────────────────────────────────────────────
interface StatusConfig {
  label: string;
  textColor: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getPm25Status(v: number): StatusConfig {
  if (v <= 30)
    return { label: '좋음', textColor: 'text-emerald-500' };
  if (v <= 80)
    return { label: '보통', textColor: 'text-blue-500' };
  if (v <= 150)
    return { label: '나쁨', textColor: 'text-red-500' };
  return { label: '매우 나쁨', textColor: 'text-red-600' };
}

function getHumidityStatus(v: number): StatusConfig {
  if (v < 30)
    return { label: '건조', textColor: 'text-yellow-500' };
  if (v <= 60)
    return { label: '쾌적', textColor: 'text-emerald-500' };
  return { label: '습함', textColor: 'text-blue-500' };
}

// ── Sub-component ─────────────────────────────────────────────────────────────
interface EnvCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  unit: string;
  status: StatusConfig;
}

function EnvCard({ icon, label, value, unit, status }: EnvCardProps) {
  return (
    <AppCard className="relative flex flex-1 flex-col gap-3 overflow-hidden p-4">
      <div className="pointer-events-none absolute -right-4 -top-4 h-24 w-24 rounded-full bg-brand-subtle blur-sm" />

      <div className="flex items-center gap-2 text-fg-muted">
        {icon}
        <span className="text-sm">{label}</span>
      </div>

      <div className="flex items-baseline gap-2 pt-2">
        <span className="text-4xl font-bold tracking-tight text-fg-strong">
          {value}
        </span>
        <span className="text-sm text-fg-muted">{unit}</span>
        <span className={cn('text-sm', status.textColor)}>{status.label}</span>
      </div>
    </AppCard>
  );
}

// ── Section ───────────────────────────────────────────────────────────────────
export default function EnvironmentSummarySection() {
  const { data: rooms, isLoading } = useRoomDataQuery();

  if (isLoading) {
    return (
      <section>
        <SectionHeader>실내 환경</SectionHeader>
        <div className="flex justify-center p-6"><Spinner className="shadow-sm" /></div>
      </section>
    );
  }

  // 모든 방의 조건 데이터를 취합해 평균값 계산 (임시 로직)
  let pm25 = 0;
  let humidity = 0;

  if (rooms && rooms.length > 0) {
    let validRoomsCount = 0;
    for (const room of rooms) {
      if (room.condition) {
        pm25 += room.condition.fineDust;
        humidity += room.condition.humidity;
        validRoomsCount++;
      }
    }
    if (validRoomsCount > 0) {
      pm25 = Math.round(pm25 / validRoomsCount);
      humidity = Math.round(humidity / validRoomsCount);
    }
  }

  return (
    <section>
      <SectionHeader>실내 환경</SectionHeader>

      <div className="px-4">
        <div className="flex gap-3">
          <EnvCard
            icon={<Icon icon={ChartBubble02Icon} size="xs" color="brand" />}
            label="미세먼지"
            value={pm25}
            unit="μg/m³"
            status={getPm25Status(pm25)}
          />
          <EnvCard
            icon={<Icon icon={DropletIcon} size="xs" color="brand" />}
            label="습도"
            value={humidity}
            unit="%"
            status={getHumidityStatus(humidity)}
          />
        </div>

        {/* <SectionLinkFooter to="/environment">상세 보기</SectionLinkFooter> */}
      </div>
    </section>
  );
}
