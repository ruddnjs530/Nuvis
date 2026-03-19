import React, { useState, useRef, useEffect } from "react";
import {
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Mic,
  Send,
  Play,
  Pause,
  Wifi,
  WifiOff,
  Camera,
  Maximize2,
  MapPin,
  Layers,
  Navigation,
  RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Map() {
  const [ros2Connected, setRos2Connected] = useState(true);
  const [isAutonomous, setIsAutonomous] = useState(false);
  const [command, setCommand] = useState("");
  const [logs, setLogs] = useState([
    "[ROS2] /nuvis/cmd_vel 연결됨",
    "[SLAM] 지도 데이터 수신 중...",
    "[NAV2] 목표 지점 설정 대기 중",
  ]);
  const [isListening, setIsListening] = useState(false);
  const canvasRef = useRef(null);
  const robotPos = useRef({ x: 0.52, y: 0.45 });
  const animFrameRef = useRef();

  // Draw SLAM map on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const draw = () => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      // Background (unexplored area)
      ctx.fillStyle = "#E8EDF2";
      ctx.fillRect(0, 0, w, h);

      // Grid
      ctx.strokeStyle = "#D1D8E0";
      ctx.lineWidth = 0.5;
      const gridSize = 20;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Explored floor area
      ctx.fillStyle = "#F7F9FC";
      // Main room
      ctx.beginPath();
      ctx.roundRect(w * 0.12, h * 0.1, w * 0.76, h * 0.55, 4);
      ctx.fill();
      // Hallway
      ctx.fillRect(w * 0.38, h * 0.6, w * 0.24, h * 0.2);
      // Side room
      ctx.beginPath();
      ctx.roundRect(w * 0.62, h * 0.35, w * 0.26, h * 0.35, 4);
      ctx.fill();

      // Walls
      ctx.strokeStyle = "#2C3E50";
      ctx.lineWidth = 3;
      ctx.lineJoin = "round";
      // Outer walls
      ctx.beginPath();
      ctx.moveTo(w * 0.12, h * 0.1);
      ctx.lineTo(w * 0.88, h * 0.1);
      ctx.lineTo(w * 0.88, h * 0.7);
      ctx.lineTo(w * 0.62, h * 0.7);
      ctx.lineTo(w * 0.62, h * 0.8);
      ctx.lineTo(w * 0.38, h * 0.8);
      ctx.lineTo(w * 0.38, h * 0.65);
      ctx.lineTo(w * 0.12, h * 0.65);
      ctx.closePath();
      ctx.stroke();

      // Interior walls
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(w * 0.62, h * 0.1);
      ctx.lineTo(w * 0.62, h * 0.35);
      ctx.stroke();

      // Door openings (gaps in walls)
      ctx.strokeStyle = "#F7F9FC";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(w * 0.62, h * 0.5);
      ctx.lineTo(w * 0.62, h * 0.6);
      ctx.stroke();

      // Furniture (obstacles)
      const furniture = [
        { x: 0.18, y: 0.18, w: 0.18, h: 0.12, label: "소파", color: "#B8C4D0" },
        { x: 0.38, y: 0.15, w: 0.14, h: 0.14, label: "테이블", color: "#C5CACD" },
        { x: 0.68, y: 0.38, w: 0.14, h: 0.2, label: "침대", color: "#B8C4D0" },
      ];
      furniture.forEach((f) => {
        ctx.fillStyle = f.color;
        ctx.beginPath();
        ctx.roundRect(w * f.x, h * f.y, w * f.w, h * f.h, 4);
        ctx.fill();
        ctx.fillStyle = "#8E9BAA";
        ctx.font = "9px -apple-system, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(f.label, w * (f.x + f.w / 2), h * (f.y + f.h / 2) + 3);
      });

      // Robot path (dotted trail)
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = "#0A84FF60";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(w * 0.88, h * 0.65);
      ctx.lineTo(w * 0.7, h * 0.65);
      ctx.lineTo(w * 0.55, h * 0.5);
      ctx.lineTo(w * robotPos.current.x, h * robotPos.current.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Robot position
      const rx = w * robotPos.current.x;
      const ry = h * robotPos.current.y;

      // Radar pulse
      const now = Date.now() / 1000;
      const pulse = (Math.sin(now * 2) * 0.5 + 0.5) * 0.5 + 0.5;
      ctx.beginPath();
      ctx.arc(rx, ry, 20 * pulse, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(10, 132, 255, ${0.12 * pulse})`;
      ctx.fill();

      // Robot circle
      ctx.beginPath();
      ctx.arc(rx, ry, 12, 0, Math.PI * 2);
      ctx.fillStyle = "#0A84FF";
      ctx.fill();
      ctx.strokeStyle = "white";
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Robot direction arrow
      ctx.fillStyle = "white";
      ctx.font = "bold 11px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("▲", rx, ry + 4);

      // Charging station
      ctx.beginPath();
      ctx.arc(w * 0.86, h * 0.63, 8, 0, Math.PI * 2);
      ctx.fillStyle = "#34C759";
      ctx.fill();
      ctx.fillStyle = "white";
      ctx.font = "bold 9px sans-serif";
      ctx.fillText("⚡", w * 0.86, h * 0.63 + 3.5);

      // Room labels
      ctx.fillStyle = "#8E9BAA";
      ctx.font = "10px -apple-system, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("거실", w * 0.38, h * 0.57);
      ctx.fillText("침실", w * 0.75, h * 0.57);
      ctx.fillText("복도", w * 0.5, h * 0.74);

      animFrameRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  const handleCommand = (e) => {
    e.preventDefault();
    if (!command.trim()) return;
    setLogs((prev) => [`[CMD] ${command}`, ...prev.slice(0, 4)]);
    setCommand("");
  };

  const sendMove = (dir) => {
    setLogs((prev) => [`[MOVE] ${dir} 방향 이동 명령 전송`, ...prev.slice(0, 4)]);
  };

  return (
    <div className="flex flex-col h-full bg-[#f8f9fa] min-h-screen pb-24">
      {/* ROS2 Connection Header */}
      <div className="px-4 pt-4 pb-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-[#8E8E93] tracking-wide uppercase">Live Control</p>
            <h1 className="text-[22px] font-semibold text-[#1C1C1E]">지도 & 제어</h1>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                ros2Connected
                  ? "bg-[#D1F5D3] text-[#1A7A2E]"
                  : "bg-[#FFE5E5] text-[#CC0000]"
              }`}
            >
              {ros2Connected ? <Wifi size={11} /> : <WifiOff size={11} />}
              {ros2Connected ? "ROS2 Connected" : "Reconnecting..."}
            </div>
            <button
              onClick={() => setRos2Connected(!ros2Connected)}
              className="w-8 h-8 rounded-full bg-[#F2F2F7] flex items-center justify-center"
            >
              <RefreshCw size={14} className="text-[#3C3C43]" />
            </button>
          </div>
        </div>
      </div>

      {/* SLAM Map */}
      <div className="mx-4 relative rounded-[20px] overflow-hidden bg-[#E8EDF2]" style={{ height: 220 }}>
        <canvas
          ref={canvasRef}
          width={380}
          height={220}
          className="w-full h-full"
          style={{ imageRendering: "crisp-edges" }}
        />

        {/* Map Controls */}
        <div className="absolute top-2.5 right-2.5 flex flex-col gap-1.5">
          <button className="w-8 h-8 bg-white/90 backdrop-blur-sm rounded-xl shadow flex items-center justify-center">
            <Layers size={14} className="text-[#1C1C1E]" />
          </button>
          <button className="w-8 h-8 bg-white/90 backdrop-blur-sm rounded-xl shadow flex items-center justify-center">
            <MapPin size={14} className="text-[#0A84FF]" />
          </button>
          <button className="w-8 h-8 bg-white/90 backdrop-blur-sm rounded-xl shadow flex items-center justify-center">
            <Maximize2 size={14} className="text-[#1C1C1E]" />
          </button>
        </div>

        {/* Camera PIP */}
        <div className="absolute top-2.5 left-2.5 w-[90px] h-[68px] rounded-2xl overflow-hidden border-2 border-white shadow-lg bg-[#0A0A0A]">
          <div className="w-full h-full flex flex-col items-center justify-center gap-1 relative">
            {/* Simulated camera feed */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#1a1a2e] to-[#0A0A1A]" />
            <div className="relative z-10 flex flex-col items-center gap-1">
              <Camera size={16} className="text-white/60" />
              <p className="text-white/60 text-[8px]">카메라 뷰</p>
            </div>
            {/* Simulated scan lines */}
            <div className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: "repeating-linear-gradient(transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)",
              }}
            />
            <div className="absolute top-1 left-1 flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[7px] text-white/70 font-medium">LIVE</span>
            </div>
          </div>
        </div>

        {/* Autonomous Drive Button */}
        <div className="absolute bottom-2.5 left-1/2 -translate-x-1/2">
          <button
            onClick={() => setIsAutonomous(!isAutonomous)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold shadow-lg transition-all ${
              isAutonomous
                ? "bg-[#FF3B30] text-white"
                : "bg-[#0A84FF] text-white"
            }`}
          >
            {isAutonomous ? <Pause size={12} /> : <Play size={12} />}
            {isAutonomous ? "자율주행 정지" : "자율주행 시작"}
          </button>
        </div>
      </div>

      {/* Manual D-pad Control */}
      <div className="mx-4 mt-3 bg-white rounded-[20px] p-4 shadow-sm mb-4">
        <div className="flex items-start gap-4">
          <div className="flex flex-col items-center">
            <p className="text-xs text-[#8E8E93] font-medium mb-2">수동 조작</p>
            <div className="relative w-[108px] h-[108px]">
              {/* Up */}
              <button
                onPointerDown={() => sendMove("전진")}
                className="absolute top-0 left-1/2 -translate-x-1/2 w-9 h-9 bg-[#F2F2F7] rounded-2xl flex items-center justify-center active:bg-[#E0E0E6] active:scale-95 transition-all"
              >
                <ChevronUp size={20} className="text-[#1C1C1E]" />
              </button>
              {/* Left */}
              <button
                onPointerDown={() => sendMove("좌회전")}
                className="absolute left-0 top-1/2 -translate-y-1/2 w-9 h-9 bg-[#F2F2F7] rounded-2xl flex items-center justify-center active:bg-[#E0E0E6] active:scale-95 transition-all"
              >
                <ChevronLeft size={20} className="text-[#1C1C1E]" />
              </button>
              {/* Center */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-9 h-9 bg-[#1C1C1E] rounded-2xl flex items-center justify-center">
                <Navigation size={16} className="text-white" />
              </div>
              {/* Right */}
              <button
                onPointerDown={() => sendMove("우회전")}
                className="absolute right-0 top-1/2 -translate-y-1/2 w-9 h-9 bg-[#F2F2F7] rounded-2xl flex items-center justify-center active:bg-[#E0E0E6] active:scale-95 transition-all"
              >
                <ChevronRight size={20} className="text-[#1C1C1E]" />
              </button>
              {/* Down */}
              <button
                onPointerDown={() => sendMove("후진")}
                className="absolute bottom-0 left-1/2 -translate-x-1/2 w-9 h-9 bg-[#F2F2F7] rounded-2xl flex items-center justify-center active:bg-[#E0E0E6] active:scale-95 transition-all"
              >
                <ChevronDown size={20} className="text-[#1C1C1E]" />
              </button>
            </div>
          </div>

          {/* Command Log */}
          <div className="flex-1 min-w-0">
            <p className="text-xs text-[#8E8E93] font-medium mb-2">ROS2 로그</p>
            <div className="bg-[#0A0A1A] rounded-2xl p-2.5 h-[108px] overflow-hidden">
              <div className="flex flex-col gap-1.5 justify-end h-full">
                <AnimatePresence>
                  {logs.slice(0, 4).map((log, i) => (
                    <motion.p
                      key={`${log}-${i}`}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="text-[9px] font-mono text-green-400 truncate"
                    >
                      {log}
                    </motion.p>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>

        {/* Command Input */}
        <form onSubmit={handleCommand} className="flex gap-2 mt-3">
          <div className="flex-1 flex items-center gap-2 bg-[#F2F2F7] rounded-2xl px-3 py-2">
            <span className="text-[#0A84FF] text-xs font-mono font-bold">$</span>
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="ROS2 명령어 입력..."
              className="flex-1 bg-transparent text-sm text-[#1C1C1E] placeholder:text-[#8E8E93] outline-none"
            />
          </div>
          <button
            type="button"
            onClick={() => {
              setIsListening(!isListening);
              if (!isListening) {
                setTimeout(() => setIsListening(false), 3000);
              }
            }}
            className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-all ${
              isListening ? "bg-[#FF3B30]" : "bg-[#F2F2F7]"
            }`}
          >
            <Mic size={16} className={isListening ? "text-white" : "text-[#3C3C43]"} />
          </button>
          <button
            type="submit"
            className="w-10 h-10 rounded-2xl bg-[#0A84FF] flex items-center justify-center"
          >
            <Send size={15} className="text-white" />
          </button>
        </form>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-center"
          >
            <p className="text-xs text-[#FF3B30] animate-pulse">🎙️ 음성 인식 중...</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
