import type { ReactNode } from 'react';
import { cn } from '~/lib/utils';

interface AppCardProps {
  children: ReactNode;
  className?: string;
}

/**
 * 프로젝트 공통 카드 래퍼
 */
export default function AppCard({ children, className }: AppCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border-default bg-surface shadow-card',
        className,
      )}
    >
      {children}
    </div>
  );
}
