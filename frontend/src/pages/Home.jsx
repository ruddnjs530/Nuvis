import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Power,
  Navigation,
  Zap,
  RotateCcw,
  Battery,
  Filter,
  Wind,
  Droplets,
  CloudRain,
  Cpu,
  ChevronRight,
  Bell,
  Settings,
} from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  const navigate = useNavigate();
  const [powerOn, setPowerOn] = useState(true);
  const [boostMode, setBoostMode] = useState(false);

  return (
    <div className="flex flex-col gap-4 px-4 pt-4 pb-4 min-h-full pb-24">
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <p className="text-xs text-[#8E8E93] tracking-wide uppercase">NUVIS</p>
          <h1 className="text-[22px] font-semibold text-[#1C1C1E]">홈 대시보드</h1>
        </div>
        <div className="flex gap-2">
          <button className="w-9 h-9 rounded-full bg-[#F2F2F7] flex items-center justify-center">
            <Bell size={18} className="text-[#3C3C43]" />
          </button>
          <button 
            onClick={() => navigate('/settings')}
            className="w-9 h-9 rounded-full bg-[#F2F2F7] flex items-center justify-center"
          >
            <Settings size={18} className="text-[#3C3C43]" />
          </button>
        </div>
      </div>

      {/* Air Quality Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-[24px] overflow-hidden cursor-pointer"
        style={{
          background: "linear-gradient(135deg, #1259C3 0%, #0A84FF 60%, #34AADC 100%)",
        }}
        onClick={() => navigate('/data')}
      >
        <div className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-white/70 text-xs mb-1">실내 공기질 상태</p>
              <h2 className="text-white text-[28px] font-bold leading-none mb-1">쾌적합니다 😊</h2>
              <p className="text-white/80 text-sm mt-2">AQI 22 · 매우좋음</p>
            </div>
            <div className="bg-white/20 rounded-2xl p-3 backdrop-blur-sm">
              <Wind size={28} className="text-white" />
            </div>
          </div>

          <div className="flex gap-3 mt-4">
            <div className="flex-1 bg-white/15 rounded-2xl p-3 backdrop-blur-sm">
              <div className="flex items-center gap-1.5 mb-1">
                <div className="w-2 h-2 rounded-full bg-green-300" />
                <p className="text-white/70 text-xs">외부 PM2.5</p>
              </div>
              <p className="text-white font-semibold text-lg leading-none">15</p>
              <p className="text-white/60 text-xs mt-0.5">μg/m³ · 좋음</p>
            </div>
            <div className="flex-1 bg-white/15 rounded-2xl p-3 backdrop-blur-sm">
              <div className="flex items-center gap-1.5 mb-1">
                <CloudRain size={12} className="text-white/70" />
                <p className="text-white/70 text-xs">강수 확률</p>
              </div>
              <p className="text-white font-semibold text-lg leading-none">0%</p>
              <p className="text-white/60 text-xs mt-0.5">맑음 · 쾌청</p>
            </div>
            <div className="flex-1 bg-white/15 rounded-2xl p-3 backdrop-blur-sm">
              <div className="flex items-center gap-1.5 mb-1">
                <Droplets size={12} className="text-white/70" />
                <p className="text-white/70 text-xs">실내 습도</p>
              </div>
              <p className="text-white font-semibold text-lg leading-none">48%</p>
              <p className="text-white/60 text-xs mt-0.5">적정 수준</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* NUVIS Robot Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="bg-white rounded-[24px] p-5 shadow-sm"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #1C1C1E, #3C3C43)" }}
            >
              <Cpu size={22} className="text-white" />
            </div>
            <div>
              <h3 className="text-[17px] font-semibold text-[#1C1C1E]">NUVIS</h3>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div
                  className={`w-2 h-2 rounded-full ${powerOn ? "bg-green-500" : "bg-gray-400"}`}
                  style={{ boxShadow: powerOn ? "0 0 6px rgba(52,199,89,0.8)" : "none" }}
                />
                <p className="text-xs text-[#8E8E93]">{powerOn ? "작동 중 · 순찰 모드" : "대기 중"}</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => navigate("/map")}
            className="text-[#0070CC] text-sm flex items-center gap-0.5"
          >
            상세 <ChevronRight size={14} />
          </button>
        </div>

        {/* Battery */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <Battery size={15} className="text-[#34C759]" />
              <span className="text-sm text-[#3C3C43]">배터리 잔량</span>
            </div>
            <span className="text-sm font-semibold text-[#1C1C1E]">85%</span>
          </div>
          <div className="h-2 bg-[#F2F2F7] rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "85%" }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="h-full rounded-full bg-gradient-to-r from-[#34C759] to-[#30D158]"
            />
          </div>
        </div>

        {/* Filter */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <Filter size={15} className="text-[#0A84FF]" />
              <span className="text-sm text-[#3C3C43]">H13 헤파 필터 수명</span>
            </div>
            <span className="text-sm font-semibold text-[#1C1C1E]">92%</span>
          </div>
          <div className="h-2 bg-[#F2F2F7] rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "92%" }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="h-full rounded-full bg-gradient-to-r from-[#0A84FF] to-[#34AADC]"
            />
          </div>
        </div>

        {/* Module Info */}
        <div className="flex items-center gap-3 mt-4 p-3 bg-[#F2F2F7] rounded-2xl">
          <div className="w-8 h-8 bg-white rounded-xl flex items-center justify-center shadow-sm">
            <Filter size={14} className="text-[#0A84FF]" />
          </div>
          <div className="flex-1">
            <p className="text-xs text-[#8E8E93]">장착 모듈</p>
            <p className="text-sm font-medium text-[#1C1C1E]">H13 HEPA 필터 모듈</p>
          </div>
          <span className="text-xs text-[#34C759] bg-[#D1F5D3] px-2 py-0.5 rounded-full font-medium">정상</span>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="bg-white rounded-[24px] p-5 shadow-sm"
      >
        <h3 className="text-[15px] font-semibold text-[#1C1C1E] mb-4">빠른 실행</h3>
        <div className="grid grid-cols-4 gap-3">
          {/* Power */}
          <button
            onClick={() => setPowerOn(!powerOn)}
            className="flex flex-col items-center gap-2"
          >
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                powerOn
                  ? "bg-gradient-to-br from-[#1259C3] to-[#0A84FF] shadow-md"
                  : "bg-[#F2F2F7]"
              }`}
            >
              <Power size={22} className={powerOn ? "text-white" : "text-[#8E8E93]"} />
            </div>
            <span className="text-xs text-[#3C3C43] font-medium">전원</span>
          </button>

          {/* Call */}
          <button
            onClick={() => navigate("/map")}
            className="flex flex-col items-center gap-2"
          >
            <div className="w-14 h-14 rounded-2xl bg-[#F2F2F7] flex items-center justify-center">
              <Navigation size={22} className="text-[#0A84FF]" />
            </div>
            <span className="text-xs text-[#3C3C43] font-medium">호출</span>
          </button>

          {/* Boost Mode */}
          <button
            onClick={() => setBoostMode(!boostMode)}
            className="flex flex-col items-center gap-2"
          >
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                boostMode
                  ? "bg-gradient-to-br from-[#FF9500] to-[#FF6B00] shadow-md"
                  : "bg-[#F2F2F7]"
              }`}
            >
              <Zap size={22} className={boostMode ? "text-white" : "text-[#FF9500]"} />
            </div>
            <span className="text-xs text-[#3C3C43] font-medium">강력모드</span>
          </button>

          {/* Return */}
          <button className="flex flex-col items-center gap-2">
            <div className="w-14 h-14 rounded-2xl bg-[#F2F2F7] flex items-center justify-center">
              <RotateCcw size={22} className="text-[#5856D6]" />
            </div>
            <span className="text-xs text-[#3C3C43] font-medium">복귀</span>
          </button>
        </div>
      </motion.div>

      {/* Recent Activity Preview */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="bg-white rounded-[24px] p-5 shadow-sm"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[15px] font-semibold text-[#1C1C1E]">최근 활동</h3>
          <button
            onClick={() => navigate("/schedule")}
            className="text-[#0070CC] text-sm flex items-center gap-0.5"
          >
            전체 <ChevronRight size={14} />
          </button>
        </div>
        <div className="flex flex-col gap-3">
          {[
            { time: "13:45", action: "순찰 완료 — 거실 영역", icon: "✅", color: "#34C759" },
            { time: "12:30", action: "강력 모드 자동 실행 (PM2.5 감지)", icon: "⚡", color: "#FF9500" },
            { time: "11:15", action: "충전 완료 (85% → 100%)", icon: "🔋", color: "#0A84FF" },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-base"
                style={{ background: `${item.color}18` }}
              >
                {item.icon}
              </div>
              <div className="flex-1">
                <p className="text-sm text-[#1C1C1E]">{item.action}</p>
                <p className="text-xs text-[#8E8E93]">오늘 {item.time}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
