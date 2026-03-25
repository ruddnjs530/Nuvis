import { BatteryFullIcon } from '@hugeicons/core-free-icons';

import AppCard from '~/components/common/app-card';
import BrandPillButton from '~/components/common/brand-pill-button';
import Icon from '~/components/common/icon';
import SectionHeader from '~/components/common/section-header';
import Spinner from '~/components/common/spinner';

import { useRobotStatusQuery } from '../api/queries';

const MAP_NATURAL_W = 637;
const MAP_NATURAL_H = 416;

const VIEWPORT_W = 378;
const VIEWPORT_H = 220;

const MAP_RENDER_W = VIEWPORT_W * 1.5;
const MAP_RENDER_H = Math.round(MAP_RENDER_W * (MAP_NATURAL_H / MAP_NATURAL_W));

function FloorMap({ position }: { position: { x: number; y: number } }) {
  const robotPxX = position.x * MAP_RENDER_W;
  const robotPxY = position.y * MAP_RENDER_H;

  const offsetX = VIEWPORT_W / 2 - robotPxX;
  const offsetY = VIEWPORT_H / 2 - robotPxY;

  const clampedX = Math.min(0, Math.max(VIEWPORT_W - MAP_RENDER_W, offsetX));
  const clampedY = Math.min(0, Math.max(VIEWPORT_H - MAP_RENDER_H, offsetY));

  const markerX = robotPxX + clampedX;
  const markerY = robotPxY + clampedY;

  return (
    <div
      className="relative overflow-hidden bg-white"
      style={{ width: VIEWPORT_W, height: VIEWPORT_H }}
      aria-label="로봇 위치 맵"
    >
      <img
        src="/map.png"
        alt="실내 지도"
        className="absolute select-none pointer-events-none max-w-none"
        style={{
          width: MAP_RENDER_W,
          height: MAP_RENDER_H,
          left: clampedX,
          top: clampedY,
          transition: 'left 0.3s ease, top 0.3s ease',
        }}
        draggable={false}
      />

      {/* 로봇 마커 */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none"
        style={{
          left: markerX,
          top: markerY,
          transition: 'left 0.3s ease, top 0.3s ease',
        }}
      >
        <div className="absolute -inset-2 rounded-full bg-brand/20 animate-ping" />
        <div className="relative h-4 w-4 rounded-full bg-brand shadow-lg ring-2 ring-white">
          <div className="absolute inset-1 rounded-full bg-white/60" />
        </div>
      </div>
    </div>
  );
}

export default function RobotStatusSection() {
  const { data: robotStatus, isLoading } = useRobotStatusQuery();

  if (isLoading) {
    return (
      <section>
        <SectionHeader>로봇 상태</SectionHeader>
        <AppCard className="flex items-center justify-center p-12">
          <Spinner className="shadow-sm" />
        </AppCard>
      </section>
    );
  }

  const battery = robotStatus ? Math.floor(robotStatus.batteryPct) : 0;
  // 임의 변환: 100% = 12시간 기준
  const totalMinutes = Math.floor((battery / 100) * 12 * 60);
  const batteryHours = Math.floor(totalMinutes / 60);
  const batteryMinutes = totalMinutes % 60;

  // API 로봇 위치
  const position = robotStatus ? { x: robotStatus.pose.x, y: robotStatus.pose.y } : { x: 0.5, y: 0.5 };

  // 로봇 모듈 정보 (API에서 제공 안되면 하드코딩 또는 다른 매핑)
  const attachedModule = '공기청정기';

  return (
    <section>
      <SectionHeader>로봇 상태</SectionHeader>

      <div className="px-4">
        <AppCard className="overflow-hidden">

          <FloorMap position={position} />

          <div className="flex flex-col gap-4 p-4">

            {/* 장착 모듈 + 상태 보기 버튼 */}
            <div className="flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <span className="text-sm text-fg-muted">장착된 모듈</span>
                <span className="text-lg font-bold text-fg-strong">
                  {attachedModule}
                </span>
              </div>
              <BrandPillButton className="h-[40px] px-4">
                상태 보기
              </BrandPillButton>
            </div>

            <div className="h-px w-full bg-border-default" />

            {/* 배터리 */}
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-fg-default">
                  <Icon icon={BatteryFullIcon} size="sm" />
                  <span className="text-sm">배터리</span>
                </div>
                <span className="text-sm font-bold text-fg-strong">
                  {battery}
                  %
                </span>
              </div>

              <div className="relative h-3 w-full overflow-hidden rounded-full bg-surface-sunken">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-brand transition-all"
                  style={{ width: `${battery}%` }}
                />
              </div>

              <p className="pt-1 text-xs text-fg-muted">
                앞으로 약
                {' '}
                {batteryHours}
                시간
                {' '}
                {batteryMinutes}
                분 사용할 수 있습니다.
              </p>
            </div>
          </div>
        </AppCard>
      </div>
    </section>
  );
}
