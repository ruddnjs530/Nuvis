import React, { useState } from "react";
import {
  Sparkles,
  Wind,
  Droplets,
  Activity,
  ChevronRight,
  Plus,
  Clock,
  CheckCircle2,
  Circle,
  CalendarClock,
  Zap,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const DAYS = ["S", "M", "T", "W", "T", "F", "S"];
const DAY_LABELS = ["일", "월", "화", "수", "목", "금", "토"];

export default function Schedule() {
  const today = new Date();
  const [selectedDay, setSelectedDay] = useState(today.getDay());
  const [aiExpanded, setAiExpanded] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  const getDateForDay = (dayIndex) => {
    const date = new Date();
    const diff = dayIndex - today.getDay();
    date.setDate(today.getDate() + diff);
    return date.getDate();
  };

  const [rules, setRules] = useState([
    {
      id: "pm25",
      label: "미세먼지 자동 실행",
      condition: "PM2.5 농도",
      threshold: "> 30 μg/m³",
      enabled: true,
      icon: <Wind size={16} />,
      color: "#FF9500",
      bg: "#FFF3E0",
    },
    {
      id: "humidity",
      label: "습도 초과 자동 실행",
      condition: "실내 습도",
      threshold: "> 60%",
      enabled: false,
      icon: <Droplets size={16} />,
      color: "#34AADC",
      bg: "#E3F4FD",
    },
    {
      id: "co2",
      label: "CO₂ 자동 환기 모드",
      condition: "CO₂ 농도",
      threshold: "> 1000 ppm",
      enabled: true,
      icon: <Activity size={16} />,
      color: "#5856D6",
      bg: "#EEF0FF",
    },
  ]);

  const [schedules] = useState([
    {
      time: "07:30",
      label: "아침 청정 순찰",
      days: [1, 2, 3, 4, 5],
      mode: "표준 모드",
      active: true,
    },
    {
      time: "12:00",
      label: "점심 집중 청정",
      days: [0, 6],
      mode: "강력 모드",
      active: true,
    },
    {
      time: "22:00",
      label: "취침 전 순찰",
      days: [0, 1, 2, 3, 4, 5, 6],
      mode: "저소음 모드",
      active: false,
    },
  ]);

  const toggleRule = (id) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r))
    );
  };

  return (
    <div className="flex flex-col gap-4 px-4 pt-4 pb-24 min-h-screen bg-[#F5F7FA]">
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <p className="text-xs text-[#8E8E93] tracking-wide uppercase">Automation</p>
          <h1 className="text-[22px] font-semibold text-[#1C1C1E]">스케줄 & 자동화</h1>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="w-9 h-9 rounded-full bg-[#0A84FF] flex items-center justify-center shadow-md"
        >
          <Plus size={18} className="text-white" />
        </button>
      </div>

      {/* Weekly Calendar Bar */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-[24px] p-4 shadow-sm border border-gray-100"
      >
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold text-[#1C1C1E]">
            {today.toLocaleDateString("ko-KR", { year: "numeric", month: "long" })}
          </p>
          <button className="text-xs text-[#0A84FF] flex items-center gap-0.5">
            월간 보기 <ChevronRight size={12} />
          </button>
        </div>
        <div className="grid grid-cols-7 gap-1">
          {DAYS.map((d, i) => {
            const dateNum = getDateForDay(i);
            const isSelected = selectedDay === i;
            const isToday = i === today.getDay();
            return (
              <button
                key={i}
                onClick={() => setSelectedDay(i)}
                className="flex flex-col items-center gap-1"
              >
                <span
                  className={`text-xs font-medium ${
                    i === 0 ? "text-[#FF3B30]" : i === 6 ? "text-[#0A84FF]" : "text-[#8E8E93]"
                  }`}
                >
                  {DAY_LABELS[i]}
                </span>
                <div
                  className={`w-9 h-9 rounded-2xl flex items-center justify-center text-sm font-semibold transition-all ${
                    isSelected
                      ? "bg-[#0A84FF] text-white shadow-md"
                      : isToday
                      ? "bg-[#E8F3FF] text-[#0A84FF]"
                      : "text-[#1C1C1E]"
                  }`}
                >
                  {dateNum}
                </div>
                {/* Schedule dots */}
                <div className="flex gap-0.5">
                  {schedules.filter((s) => s.days.includes(i)).slice(0, 3).map((_, si) => (
                    <div
                      key={si}
                      className={`w-1 h-1 rounded-full ${isSelected ? "bg-white/70" : "bg-[#0A84FF]"}`}
                    />
                  ))}
                </div>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Scheduled Tasks */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-[24px] p-4 shadow-sm border border-gray-100"
      >
        <p className="text-sm font-semibold text-[#1C1C1E] mb-3">
          {DAY_LABELS[selectedDay]}요일 스케줄
        </p>
        <div className="flex flex-col gap-3">
          {schedules
            .filter((s) => s.days.includes(selectedDay))
            .map((schedule, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="flex flex-col items-center">
                  <span className="text-sm font-bold text-[#1C1C1E]">{schedule.time}</span>
                  {i < schedules.filter((s) => s.days.includes(selectedDay)).length - 1 && (
                    <div className="w-0.5 h-4 bg-[#E5E5EA] mt-1 rounded-full" />
                  )}
                </div>
                <div
                  className={`flex-1 flex items-center justify-between p-3 rounded-2xl ${
                    schedule.active ? "bg-[#F0F7FF]" : "bg-[#F2F2F7]"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                        schedule.active ? "bg-[#0A84FF]" : "bg-[#8E8E93]"
                      }`}
                    >
                      <Clock size={14} className="text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[#1C1C1E]">{schedule.label}</p>
                      <p className="text-xs text-[#8E8E93]">{schedule.mode}</p>
                    </div>
                  </div>
                  {schedule.active ? (
                    <CheckCircle2 size={18} className="text-[#34C759]" />
                  ) : (
                    <Circle size={18} className="text-[#C7C7CC]" />
                  )}
                </div>
              </div>
            ))}
          {/* If no tasks for the day */}
          {schedules.filter((s) => s.days.includes(selectedDay)).length === 0 && (
            <div className="text-center py-6 text-[#8E8E93] text-sm">
              설정된 스케줄이 없습니다.
            </div>
          )}
        </div>
      </motion.div>

      {/* AI Suggestion Banner */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="rounded-[24px] overflow-hidden"
        style={{
          background: "linear-gradient(135deg, #5856D6, #AF52DE)",
        }}
      >
        <button
          className="w-full p-4 text-left"
          onClick={() => setAiExpanded(!aiExpanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-2xl backdrop-blur-sm flex items-center justify-center">
                <Sparkles size={20} className="text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm">AI 스케줄링 추천</p>
                <p className="text-white/70 text-xs">패턴 분석 완료 · 3개 추천</p>
              </div>
            </div>
            <motion.div
              animate={{ rotate: aiExpanded ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight size={18} className="text-white/80" />
            </motion.div>
          </div>
        </button>

        <AnimatePresence>
          {aiExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 flex flex-col gap-2.5">
                {[
                  {
                    label: "귀가 시간 30분 전 사전 청정",
                    detail: "평균 귀가 시간: 오후 6:30 감지",
                    icon: "🏠",
                  },
                  {
                    label: "주말 오전 11시 집중 모드",
                    detail: "주말 활동 패턴 기반 추천",
                    icon: "⚡",
                  },
                  {
                    label: "황사 예보 시 자동 강력 모드",
                    detail: "기상청 API 연동 자동화",
                    icon: "🌪️",
                  },
                ].map((suggestion, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between bg-white/15 rounded-2xl p-3"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="text-xl">{suggestion.icon}</span>
                      <div>
                        <p className="text-white text-xs font-medium">{suggestion.label}</p>
                        <p className="text-white/60 text-[10px]">{suggestion.detail}</p>
                      </div>
                    </div>
                    <button className="bg-white text-[#5856D6] text-[10px] font-semibold px-2.5 py-1 rounded-full">
                      적용
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Automation Rules */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-[24px] p-4 shadow-sm border border-gray-100"
      >
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold text-[#1C1C1E]">자동화 규칙 (Event CRUD)</p>
          <div className="flex items-center gap-1">
            <Zap size={12} className="text-[#FF9500]" />
            <span className="text-xs text-[#8E8E93]">
              {rules.filter((r) => r.enabled).length}개 활성
            </span>
          </div>
        </div>
        <div className="flex flex-col gap-3">
          {rules.map((rule) => (
            <motion.div
              key={rule.id}
              layout
              className="flex items-center gap-3 p-3 rounded-2xl"
              style={{ background: rule.enabled ? rule.bg : "#F2F2F7" }}
            >
              <div
                className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0"
                style={{
                  background: rule.enabled ? rule.color : "#C7C7CC",
                  color: "white",
                }}
              >
                {rule.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p
                  className="text-sm font-medium truncate"
                  style={{ color: rule.enabled ? "#1C1C1E" : "#8E8E93" }}
                >
                  {rule.label}
                </p>
                <p className="text-xs text-[#8E8E93]">
                  {rule.condition}{" "}
                  <span
                    className="font-semibold"
                    style={{ color: rule.enabled ? rule.color : "#C7C7CC" }}
                  >
                    {rule.threshold}
                  </span>
                </p>
              </div>
              {/* Custom Toggle */}
              <button
                onClick={() => toggleRule(rule.id)}
                className={`relative w-12 h-6 rounded-full transition-all duration-300 flex-shrink-0 ${
                  rule.enabled ? "" : "bg-[#E5E5EA]"
                }`}
                style={{ background: rule.enabled ? rule.color : undefined }}
              >
                <motion.div
                  animate={{ x: rule.enabled ? 24 : 2 }}
                  transition={{ duration: 0.25, type: "spring", stiffness: 500, damping: 30 }}
                  className="absolute top-1 w-4 h-4 bg-white rounded-full shadow"
                />
              </button>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Add Rule Modal */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end justify-center"
            style={{ background: "rgba(0,0,0,0.4)" }}
            onClick={() => setShowAddModal(false)}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 400, damping: 40 }}
              className="w-full bg-white rounded-t-[32px] p-6 pb-12"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-semibold text-[#1C1C1E]">새 자동화 추가</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="w-8 h-8 rounded-full bg-[#F2F2F7] flex items-center justify-center"
                >
                  <X size={16} className="text-[#3C3C43]" />
                </button>
              </div>
              <div className="flex flex-col gap-3">
                {[
                  { icon: "🌡️", label: "온도 조건 추가", desc: "실내 온도 기준 트리거" },
                  { icon: "💨", label: "VOC 조건 추가", desc: "휘발성 유기화합물 감지" },
                  { icon: "📅", label: "시간 스케줄", desc: "반복 시간 기반 자동화" },
                  { icon: "📍", label: "위치 기반 자동화", desc: "GPS 귀가 감지 트리거" },
                ].map((item, i) => (
                  <button
                    key={i}
                    className="flex items-center gap-3 p-3 rounded-2xl bg-[#F2F2F7] text-left"
                    onClick={() => setShowAddModal(false)}
                  >
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <p className="text-sm font-medium text-[#1C1C1E]">{item.label}</p>
                      <p className="text-xs text-[#8E8E93]">{item.desc}</p>
                    </div>
                    <ChevronRight size={16} className="text-[#C7C7CC] ml-auto" />
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
