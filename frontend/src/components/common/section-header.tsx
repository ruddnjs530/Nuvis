import type { ReactNode } from 'react';

interface SectionHeaderProps {
  children: ReactNode;
}

/** 대시보드 섹션 공통 헤더 */
export default function SectionHeader({ children }: SectionHeaderProps) {
  return (
    <h2 className="px-6 py-4 text-xl font-bold leading-tight tracking-tight text-fg-strong">
      {children}
    </h2>
  );
}
