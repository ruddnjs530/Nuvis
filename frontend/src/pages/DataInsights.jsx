import React, { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingDown,
  TrendingUp,
  Wind,
  Droplets,
  Activity,
  Thermometer,
  ChevronRight,
  BarChart2,
  Download,
  Filter,
} from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

const pm25Data = [
  { time: "10AM", value: 28, indoor: 12 },
  { time: "10:30", value: 32, indoor: 15 },
  { time: "11AM", value: 45, indoor: 22 },
  { time: "11:30", value: 38, indoor: 18 },
  { time: "12PM", value: 25, indoor: 14 },
  { time: "12:30", value: 20, indoor: 11 },
  { time: "1PM", value: 15, indoor: 8 },
  { time: "1:30", value: 18, indoor: 9 },
  { time: "2PM", value: 22, indoor: 10 },
  { time: "2:30", value: 30, indoor: 14 },
  { time: "3PM", value: 35, indoor: 16 },
];

const activityLogs = [
  {
    time: "13:45",
    action: "순찰 완료",
    detail: "거실 → 주방 → 침실 영역 완료",
    type: "success",
    icon: "✅",
  },
  {
    time: "12:30",
    action: "강력 모드 자동 실행",
    detail: "PM2.5 45μg/m³ 감지 (임계값 초과)",
    type: "warning",
    icon: "⚡",
  },
  {
    time: "12:00",
    action: "순찰 시작",
    detail: "예약 스케줄 점심 청정 모드",
    type: "info",
    icon: "🚀",
  },
  {
    time: "11:15",
    action: "충전 완료",
    detail: "배터리 100% → 순찰 재개",
    type: "success",
    icon: "🔋",
  },
  {
    time: "10:52",
    action: "장애물 감지",
    detail: "소파 앞 경로 재탐색 완료",
    type: "warning",
    icon: "⚠️",
  },
  {
    time: "10:30",
    action: "자동 실행",
    detail: "PM2.5 32μg/m³ → 자동화 규칙 트리거",
    type: "info",
    icon: "🤖",
  },
  {
    time: "10:00",
    action: "시스템 시작",
    detail: "NUVIS 정상 부팅 · ROS2 연결됨",
    type: "success",
    icon: "✨",
  },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1C1C1E] rounded-2xl px-3 py-2 shadow-xl">
        <p className="text-white/60 text-[10px] mb-1">{label}</p>
        <p className="text-white text-xs font-semibold">외부: {payload[0]?.value} μg/m³</p>
        <p className="text-[#34AADC] text-xs font-semibold">실내: {payload[1]?.value} μg/m³</p>
      </div>
    );
  }
  return null;
};

export default function DataInsights() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("pm25");

  const stats = [
    { label: "평균 PM2.5", value: "15", unit: "μg/m³", trend: -18, color: "#0A84FF", icon: <Wind size={14} /> },
    { label: "평균 습도", value: "48", unit: "%", trend: +3, color: "#34AADC", icon: <Droplets size={14} /> },
    { label: "평균 CO₂", value: "780", unit: "ppm", trend: -5, color: "#5856D6", icon: <Activity size={14} /> },
    { label: "평균 온도", value: "23.2", unit: "°C", trend: +1, color: "#FF9500", icon: <Thermometer size={14} /> },
  ];

  const tabData = {
    pm25: { label: "PM2.5 (μg/m³)", color: "#0A84FF", bg: "#E8F3FF" },
    humidity: { label: "습도 (%)", color: "#34AADC", bg: "#E3F4FD" },
    co2: { label: "CO₂ (ppm)", color: "#5856D6", bg: "#EEF0FF" },
    temp: { label: "온도 (°C)", color: "#FF9500", bg: "#FFF3E0" },
  };

  return (
    <div className="flex flex-col gap-4 px-4 pt-4 pb-4 min-h-screen pb-24 bg-[#F5F7FA]">
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <p className="text-xs text-[#8E8E93] tracking-wide uppercase">Analytics</p>
          <h1 className="text-[22px] font-semibold text-[#1C1C1E]">데이터 인사이트</h1>
        </div>
        <div className="flex gap-2">
          <button className="w-9 h-9 rounded-full bg-[#F2F2F7] flex items-center justify-center">
            <Filter size={16} className="text-[#3C3C43]" />
          </button>
          <button className="w-9 h-9 rounded-full bg-[#F2F2F7] flex items-center justify-center">
            <Download size={16} className="text-[#3C3C43]" />
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 gap-3"
      >
        {stats.map((stat, i) => (
          <div key={i} className="bg-white rounded-[20px] p-4 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <div
                className="w-7 h-7 rounded-xl flex items-center justify-center"
                style={{ background: `${stat.color}20`, color: stat.color }}
              >
                {stat.icon}
              </div>
              <div
                className={`flex items-center gap-0.5 text-xs font-medium ${
                  stat.trend < 0 ? "text-[#34C759]" : "text-[#FF3B30]"
                }`}
              >
                {stat.trend < 0 ? <TrendingDown size={12} /> : <TrendingUp size={12} />}
                {Math.abs(stat.trend)}%
              </div>
            </div>
            <p className="text-[22px] font-bold text-[#1C1C1E] leading-none">
              {stat.value}
              <span className="text-xs text-[#8E8E93] font-normal ml-1">{stat.unit}</span>
            </p>
            <p className="text-xs text-[#8E8E93] mt-1">{stat.label}</p>
          </div>
        ))}
      </motion.div>

      {/* Chart Card */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-[24px] p-4 shadow-sm border border-gray-100"
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-semibold text-[#1C1C1E]">지난 24시간 추이</p>
            <p className="text-xs text-[#8E8E93]">오전 10시 ~ 오후 3시</p>
          </div>
          <button className="flex items-center gap-1 text-xs text-[#0A84FF]">
            <BarChart2 size={13} />
            전체 보기
          </button>
        </div>

        {/* Tab Selector */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-1 mt-2">
          {Object.keys(tabData).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                activeTab === tab
                  ? "text-white shadow-sm"
                  : "bg-[#F2F2F7] text-[#8E8E93]"
              }`}
              style={
                activeTab === tab
                  ? { background: tabData[tab].color }
                  : undefined
              }
            >
              {tab === "pm25" ? "PM2.5" : tab === "humidity" ? "습도" : tab === "co2" ? "CO₂" : "온도"}
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="h-40 w-full mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={pm25Data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorOutdoor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={tabData[activeTab].color} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={tabData[activeTab].color} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorIndoor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#34C759" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#34C759" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid key="grid" strokeDasharray="3 3" stroke="#F2F2F7" vertical={false} />
              <XAxis
                key="xaxis"
                dataKey="time"
                tick={{ fontSize: 9, fill: "#8E8E93" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                key="yaxis"
                tick={{ fontSize: 9, fill: "#8E8E93" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip key="tooltip" content={<CustomTooltip />} />
              <Area
                key="outdoor"
                type="monotone"
                dataKey="value"
                name="outdoor"
                stroke={tabData[activeTab].color}
                strokeWidth={2}
                fill="url(#colorOutdoor)"
                dot={false}
              />
              <Area
                key="indoor"
                type="monotone"
                dataKey="indoor"
                name="indoor"
                stroke="#34C759"
                strokeWidth={2}
                fill="url(#colorIndoor)"
                dot={false}
                strokeDasharray="4 4"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-2 justify-center">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-1 rounded-full" style={{ background: tabData[activeTab].color }} />
            <span className="text-[10px] text-[#8E8E93]">외부</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 rounded-full bg-[#34C759]" style={{ borderTop: "2px dashed #34C759" }} />
            <span className="text-[10px] text-[#8E8E93]">실내 (정화 후)</span>
          </div>
        </div>
      </motion.div>

      {/* Activity Logs */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-[24px] p-4 shadow-sm border border-gray-100 mb-6"
      >
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold text-[#1C1C1E]">로봇 활동 기록</p>
          <button className="text-[#0070CC] text-xs flex items-center gap-0.5">
            전체 로그 <ChevronRight size={12} />
          </button>
        </div>
        <div className="flex flex-col">
          {activityLogs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.04 }}
              className="flex gap-3 relative"
            >
              {/* Timeline line */}
              {i < activityLogs.length - 1 && (
                <div className="absolute left-[17px] top-9 bottom-0 w-0.5 bg-[#F2F2F7]" />
              )}
              <div className="flex flex-col items-center flex-shrink-0 mt-2">
                <div className="w-9 h-9 rounded-full bg-[#F2F2F7] flex items-center justify-center text-base z-10">
                  {log.icon}
                </div>
              </div>
              <div className="flex-1 pb-4 pt-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-[#1C1C1E]">{log.action}</p>
                  <p className="text-xs text-[#8E8E93] flex-shrink-0 ml-2">오후 {log.time}</p>
                </div>
                <p className="text-xs text-[#8E8E93] mt-0.5">{log.detail}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
