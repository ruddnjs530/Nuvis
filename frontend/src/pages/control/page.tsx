import Spinner from '~/components/common/spinner';
import { useWebRTC } from './hooks/use-webrtc';

export default function ControlPage() {
  // 백엔드의 시그널링 서버 주소가 확정되면 이곳에 적어줍니다.
  // 예: 'ws://localhost:8080/signaling'
  const SIGNALING_URL = '';
  const { videoRef, isConnected, errorMsg } = useWebRTC(SIGNALING_URL);

  return (
    <div className="relative flex flex-1 flex-col bg-black overflow-hidden -mx-4 sm:mx-0">
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
      <div className="absolute top-0 left-0 right-0 flex items-start justify-between bg-gradient-to-b from-black/80 via-black/40 to-transparent p-6 pointer-events-none pb-12">
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
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center bg-black/60 p-6 text-center text-white/80 backdrop-blur-sm">
          {errorMsg
            ? (
                <div className="flex flex-col items-center gap-4">
                  <span className="drop-shadow-lg text-4xl">⚠️</span>
                  <p className="text-sm font-bold text-danger drop-shadow-md">{errorMsg}</p>
                </div>
              )
            : (
                <div className="flex flex-col items-center gap-5">
                  <Spinner variant="white" className="shadow-lg" />
                  <div className="flex flex-col gap-1.5">
                    <p className="text-base font-bold text-white drop-shadow-md">시그널링 서버 연결 대기중</p>
                    <p className="text-xs text-white/50">서버 주소가 설정되면 영상이 출력됩니다.</p>
                  </div>
                </div>
              )}
        </div>
      )}
    </div>
  );
}
