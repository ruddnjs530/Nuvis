import React, { useState } from "react";
import { useNavigate, Routes, Route } from "react-router-dom";
import {
  User,
  Cloud,
  Smartphone,
  Settings2,
  Bell,
  RefreshCw,
  HelpCircle,
  LogOut,
  ChevronRight,
  ArrowLeft,
  Plus,
  Wind,
  Droplets,
  Activity
} from "lucide-react";
import { motion } from "framer-motion";

function SettingsMenu() {
  const navigate = useNavigate();
  const [pushEnabled, setPushEnabled] = useState(true);
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(false);

  return (
    <div className="flex flex-col gap-4 px-4 pt-4 pb-24 min-h-screen bg-[#F5F7FA]">
      {/* Header */}
      <div className="flex items-center justify-between pt-2">
        <div>
          <p className="text-xs text-[#8E8E93] tracking-wide uppercase">Preferences</p>
          <h1 className="text-[22px] font-semibold text-[#1C1C1E]">설정</h1>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-4"
      >
        {/* Profile Card */}
        <div className="bg-white rounded-[24px] p-5 shadow-sm border border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-[#1259C3] to-[#0A84FF] rounded-full flex items-center justify-center shadow-md">
              <User size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#1C1C1E]">SSAFY 관리자</h2>
              <p className="text-xs text-[#8E8E93]">admin@ssafy.com</p>
            </div>
          </div>
          <button className="bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1C1C1E] px-4 py-2 rounded-full text-xs font-semibold transition-colors">
            수정
          </button>
        </div>

        {/* Device Settings Group */}
        <div>
          <h3 className="text-xs font-semibold text-[#8E8E93] ml-2 mb-2 uppercase tracking-wide">기기 및 연결</h3>
          <div className="bg-white rounded-[24px] shadow-sm border border-gray-100 overflow-hidden">
            <button className="w-full flex items-center justify-between p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#E8F3FF] flex items-center justify-center">
                  <Cloud size={18} className="text-[#0A84FF]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1E]">로봇 연결 설정</span>
              </div>
              <ChevronRight size={18} className="text-[#C7C7CC]" />
            </button>
            <button className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#FFF3E0] flex items-center justify-center">
                  <Smartphone size={18} className="text-[#FF9500]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1E]">스마트 가전 연동 (플러그)</span>
              </div>
              <ChevronRight size={18} className="text-[#C7C7CC]" />
            </button>
          </div>
        </div>

        {/* General Settings Group */}
        <div>
          <h3 className="text-xs font-semibold text-[#8E8E93] ml-2 mb-2 uppercase tracking-wide">일반 설정</h3>
          <div className="bg-white rounded-[24px] shadow-sm border border-gray-100 overflow-hidden">
            <button
              onClick={() => navigate('/settings/events')}
              className="w-full flex items-center justify-between p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#EEF0FF] flex items-center justify-center">
                  <Settings2 size={18} className="text-[#5856D6]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1E]">이벤트 CRUD (스케줄 관리)</span>
              </div>
              <ChevronRight size={18} className="text-[#C7C7CC]" />
            </button>
            <div className="w-full flex items-center justify-between p-4 border-b border-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#FFE5E5] flex items-center justify-center">
                  <Bell size={18} className="text-[#FF3B30]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1E]">푸시 알림</span>
              </div>
              <button
                onClick={() => setPushEnabled(!pushEnabled)}
                className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
                  pushEnabled ? "bg-[#34C759]" : "bg-[#E5E5EA]"
                }`}
              >
                <motion.div
                  animate={{ x: pushEnabled ? 24 : 2 }}
                  transition={{ duration: 0.25, type: "spring", stiffness: 500, damping: 30 }}
                  className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm"
                />
              </button>
            </div>
            <div className="w-full flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#D1F5D3] flex items-center justify-center">
                  <RefreshCw size={18} className="text-[#34C759]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1E]">자동 업데이트</span>
              </div>
              <button
                onClick={() => setAutoUpdateEnabled(!autoUpdateEnabled)}
                className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
                  autoUpdateEnabled ? "bg-[#34C759]" : "bg-[#E5E5EA]"
                }`}
              >
                <motion.div
                  animate={{ x: autoUpdateEnabled ? 24 : 2 }}
                  transition={{ duration: 0.25, type: "spring", stiffness: 500, damping: 30 }}
                  className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm"
                />
              </button>
            </div>
          </div>
        </div>

        {/* Other Group */}
        <div>
          <h3 className="text-xs font-semibold text-[#8E8E93] ml-2 mb-2 uppercase tracking-wide">기타</h3>
          <div className="bg-white rounded-[24px] shadow-sm border border-gray-100 overflow-hidden">
            <button className="w-full flex items-center justify-between p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#F2F2F7] flex items-center justify-center">
                  <HelpCircle size={18} className="text-[#8E8E93]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1E]">도움말 및 지원</span>
              </div>
              <ChevronRight size={18} className="text-[#C7C7CC]" />
            </button>
            <button className="w-full flex items-center p-4 hover:bg-[#FFE5E5] transition-colors group">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#FFE5E5] group-hover:bg-[#FF3B30] flex items-center justify-center transition-colors">
                  <LogOut size={18} className="text-[#FF3B30] group-hover:text-white transition-colors" />
                </div>
                <span className="text-sm font-medium text-[#FF3B30]">로그아웃</span>
              </div>
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function EventCrud() {
  const navigate = useNavigate();
  const [events, setEvents] = useState([
    { id: 'dust', enabled: true },
    { id: 'humidity', enabled: true },
    { id: 'co2', enabled: false },
  ]);

  const toggleEvent = (id) => {
    setEvents(events.map(e => e.id === id ? { ...e, enabled: !e.enabled } : e));
  };

  const getEventState = (id) => events.find(e => e.id === id)?.enabled;

  return (
    <div className="flex flex-col h-full bg-[#F5F7FA] min-h-screen z-50 fixed inset-0 overflow-y-auto w-full max-w-md mx-auto">
      {/* Header */}
      <div className="px-4 pt-4 pb-4 bg-[#F5F7FA] sticky top-0 z-20 flex items-center justify-between mb-2">
        <button
          onClick={() => navigate(-1)}
          className="w-10 h-10 rounded-full bg-[#F2F2F7] flex items-center justify-center hover:bg-[#E5E5EA] transition-colors shadow-sm"
        >
          <ArrowLeft size={20} className="text-[#1C1C1E]" />
        </button>
        <h1 className="text-[19px] font-semibold text-[#1C1C1E]">이벤트 CRUD</h1>
        <div className="w-10 h-10"></div> {/* Spacer */}
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="px-4 flex-1 space-y-3 pb-24"
      >
        {/* Dust Event */}
        <div className="bg-white rounded-[24px] p-5 shadow-sm border border-gray-100 flex items-center justify-between">
          <div className="flex-1 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#FFF3E0] flex items-center justify-center border border-orange-50">
              <Wind size={20} className="text-[#FF9500]" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-[#1C1C1E]">미세먼지 농도 조절</h3>
              <p className="text-xs text-[#8E8E93] mt-0.5">미세먼지 {'>'} 30 μg/m³</p>
            </div>
          </div>
          <button
            onClick={() => toggleEvent('dust')}
            className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
              getEventState('dust') ? "bg-[#34C759]" : "bg-[#E5E5EA]"
            }`}
          >
            <motion.div
              animate={{ x: getEventState('dust') ? 24 : 2 }}
              transition={{ duration: 0.25, type: "spring", stiffness: 500, damping: 30 }}
              className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm"
            />
          </button>
        </div>

        {/* Humidity Event */}
        <div className="bg-white rounded-[24px] p-5 shadow-sm border border-gray-100 flex items-center justify-between">
          <div className="flex-1 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#E3F4FD] flex items-center justify-center border border-blue-50">
              <Droplets size={20} className="text-[#34AADC]" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-[#1C1C1E]">습도 조절</h3>
              <p className="text-xs text-[#8E8E93] mt-0.5">습도 {'>'} 60%</p>
            </div>
          </div>
          <button
            onClick={() => toggleEvent('humidity')}
            className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
              getEventState('humidity') ? "bg-[#34AADC]" : "bg-[#E5E5EA]"
            }`}
          >
            <motion.div
              animate={{ x: getEventState('humidity') ? 24 : 2 }}
              transition={{ duration: 0.25, type: "spring", stiffness: 500, damping: 30 }}
              className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm"
            />
          </button>
        </div>

        {/* CO2 Event (Disabled initially) */}
        <div className="bg-white rounded-[24px] p-5 shadow-sm border border-gray-100 flex items-center justify-between">
          <div className="flex-1 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#EEF0FF] flex items-center justify-center border border-indigo-50">
              <Activity size={20} className="text-[#5856D6]" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-[#1C1C1E]">CO₂ 과다 환기</h3>
              <p className="text-xs text-[#8E8E93] mt-0.5">CO₂ {'>'} 1000 ppm</p>
            </div>
          </div>
          <button
            onClick={() => toggleEvent('co2')}
            className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
              getEventState('co2') ? "bg-[#5856D6]" : "bg-[#E5E5EA]"
            }`}
          >
            <motion.div
              animate={{ x: getEventState('co2') ? 24 : 2 }}
              transition={{ duration: 0.25, type: "spring", stiffness: 500, damping: 30 }}
              className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm"
            />
          </button>
        </div>
      </motion.div>

      {/* Floating Action Button (FAB) */}
      <div className="fixed bottom-8 right-6 z-30">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-14 h-14 bg-[#0A84FF] text-white rounded-full shadow-lg shadow-blue-500/30 flex justify-center items-center"
        >
          <Plus size={24} />
        </motion.button>
      </div>
    </div>
  );
}

export default function Settings() {
  return (
    <Routes>
      <Route path="/" element={<SettingsMenu />} />
      <Route path="/events" element={<EventCrud />} />
    </Routes>
  );
}
