import { Alert01Icon } from '@hugeicons/core-free-icons';
import Icon from '~/components/common/icon';
import Spinner from '~/components/common/spinner';
import { useWebRTC } from './hooks/use-webrtc';

export default function ControlPage() {
  // @ "../backend/src/modules/webrtc/services/webrtc-signaling.service.ts"
  const SESSION_ID = 'test-session-id';

  const { videoRef, isConnected, errorMsg } = useWebRTC(SESSION_ID);

  return (
    <div className="relative flex flex-1 flex-col bg-black">
      <main className="relative mx-auto flex w-full max-w-[448px] flex-1 flex-col overflow-hidden">

        {/* WebRTC Video 스트림 */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`h-full w-full flex-1 object-cover transition-opacity duration-500 ${
            isConnected ? 'opacity-100' : 'opacity-0'
          }`}
        />

        {/* 상단 오버레이 (헤더 UI) */}
        <div className="absolute left-0 right-0 top-0 flex items-start justify-between bg-gradient-to-b from-black/80 via-black/40 to-transparent p-6 pb-12 pointer-events-none">
          <h2 className="text-xl font-bold tracking-wide text-white drop-shadow-md">
            라이브 카메라
          </h2>

          {/* 연결 상태 뱃지 */}
          <div
            className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-bold backdrop-blur-md ${
              isConnected
                ? 'border-success/30 bg-success/20 text-success'
                : 'border-white/20 bg-black/50 text-white/80'
            }`}
          >
            <div
              className={`h-2 w-2 rounded-full ${
                isConnected ? 'bg-success shadow-[0_0_8px_rgba(0,255,128,1)]' : 'animate-pulse bg-white/50'
              }`}
            />
            {isConnected ? 'LIVE' : 'Connecting'}
          </div>
        </div>

        {/* 에러 및 대기중 상태 중앙 오버레이 */}
        {!isConnected && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/60 p-6 text-center text-white/80 backdrop-blur-sm pointer-events-none">
            {errorMsg
              ? (
                  <div className="flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-300">
                    <Icon icon={Alert01Icon} size="lg" color="currentColor" className="text-danger drop-shadow-lg" />
                    {/* 요청한 메시지로 변경 */}
                    <p className="text-lg font-bold text-danger drop-shadow-md">
                      {errorMsg}
                    </p>
                    <p className="text-xs text-white/40">시뮬레이터 실행 후 페이지를 새로고침해 주세요.</p>
                  </div>
                )
              : (
                  <div className="flex flex-col items-center gap-5">
                    <Spinner variant="white" className="shadow-lg" />
                    <div className="flex flex-col gap-1.5">
                      <p className="text-base font-bold text-white drop-shadow-md">스트리밍 연결 대기중</p>
                      <p className="text-xs text-white/50">연결이 완료되면 영상이 출력됩니다.</p>
                    </div>
                  </div>
                )}
          </div>
        )}
      </main>
    </div>
  );
}
