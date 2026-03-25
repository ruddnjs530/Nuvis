import type { ReactNode } from 'react';
import { cn } from '~/lib/utils';

interface BrandPillButtonProps {
  'children': ReactNode;
  'onClick'?: () => void;
  'className'?: string;
  'type'?: 'button' | 'submit' | 'reset';
  'aria-label'?: string;
}

/**
 * 브랜드 테마가 적용된 둥근(Pill) 버튼 컴포넌트
 */
export default function BrandPillButton({
  children,
  onClick,
  className,
  type = 'button',
  'aria-label': ariaLabel,
}: BrandPillButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      aria-label={ariaLabel}
      className={cn(
        'flex items-center justify-center rounded-full bg-brand-subtle text-sm text-fg-strong transition-opacity hover:opacity-70',
        className,
      )}
    >
      {children}
    </button>
  );
}
