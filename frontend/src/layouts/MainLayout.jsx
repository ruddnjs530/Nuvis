import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { HiOutlineHome, HiOutlineMap, HiOutlineCalendar, HiOutlineCog } from 'react-icons/hi';

const navItems = [
  { path: '/', label: '홈', icon: HiOutlineHome },
  { path: '/map', label: '지도', icon: HiOutlineMap },
  { path: '/schedule', label: '일정 관리', icon: HiOutlineCalendar },
  { path: '/settings', label: '설정', icon: HiOutlineCog },
];

export default function MainLayout() {
  return (
    <div className="flex flex-col h-screen w-full bg-background overflow-hidden max-w-md mx-auto shadow-xl relative">
      {/* 
        This max-w-md mx-auto makes it look like a mobile app even on desktop screens.
        For a pure fluid app, we could remove max-w-md, but mobile-first is better for this dashboard.
      */}
      
      {/* Main Content Area (Scrollable) */}
      <main className="flex-1 overflow-y-auto pb-20">
        <Outlet />
      </main>

      {/* Bottom Navigation Bar */}
      <nav className="absolute bottom-0 w-full bg-white border-t border-gray-200 px-2 py-2 flex justify-around items-center z-50 rounded-t-2xl shadow-[0_-4px_20px_rgba(0,0,0,0.05)]">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center w-16 h-14 rounded-2xl transition-all duration-200 ${
                isActive ? 'text-primary font-bold' : 'text-text-secondary hover:text-primary-dark hover:bg-gray-50'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className={`p-1.5 rounded-xl ${isActive ? 'bg-primary-light text-primary' : 'bg-transparent'}`}>
                  <item.icon className={`text-2xl ${isActive ? 'stroke-2' : 'stroke-1.5'}`} />
                </div>
                <span className="text-[10px] mt-1">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
