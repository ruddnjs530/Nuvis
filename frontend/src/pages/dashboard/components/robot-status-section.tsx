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

// 시뮬레이터 로봇 좌표 기준값
const SIM_X_MIN = -8.767;
const SIM_X_MAX = 8.513;
const SIM_Y_MIN = -5.532;
const SIM_Y_MAX = 21.121;

// ROS 좌표를 퍼센트(%)로 변환하는 함수
function convertToPercentage(poseX: number, poseY: number) {
  // 1. 가로축 (웹의 X, left): 시뮬레이터의 Y값이 담당
  // Y가 최소일 때(좌측) 0%, 최대일 때(우측) 100%
  const px = ((SIM_Y_MAX - poseY) / (SIM_Y_MAX - SIM_Y_MIN)) * 100;

  // 2. 세로축 (웹의 Y, top): 시뮬레이터의 X값이 담당
  // X가 최대일 때(상단) 0%, 최소일 때(하단) 100% (웹은 위에서 아래로 값이 커지므로 반전)
  const py = ((SIM_X_MAX - poseX) / (SIM_X_MAX - SIM_X_MIN)) * 100;

  return {
    x: Math.max(0, Math.min(100, px)),
    y: Math.max(0, Math.min(100, py)),
  };
}

function FloorMap({ position }: { position: { x: number; y: number } }) {
  const robotPxX = (position.x * MAP_RENDER_W) / 100;
  const robotPxY = (position.y * MAP_RENDER_H) / 100;

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

// API에서 영어로 오는 모듈 이름을 한국어로 매핑하기 위한 객체 (원본 복구)
const MODULE_NAME_MAP: Record<string, string> = {
  AIR_PURIFIER: '공기청정기',
};

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

  const battery = robotStatus?.batteryPct ? Math.floor(robotStatus.batteryPct) : 0;

  const totalMinutes = Math.floor((battery / 100) * 12 * 60);
  const batteryHours = Math.floor(totalMinutes / 60);
  const batteryMinutes = totalMinutes % 60;

  // 시뮬레이터 좌표를 웹 화면용 퍼센트 좌표로 변환
  const position = robotStatus
    ? convertToPercentage(robotStatus.poseX, robotStatus.poseY)
    : { x: 0, y: 0 };

  const moduleName = robotStatus?.attachedModule?.name;
  const attachedModule = moduleName ? MODULE_NAME_MAP[moduleName] || moduleName : '모듈 없음';

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
