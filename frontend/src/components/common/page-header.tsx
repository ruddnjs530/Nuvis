import type { ReactNode } from 'react';
import { Menu01Icon } from '@hugeicons/core-free-icons';
import Icon from '~/components/common/icon';

// ── Types ─────────────────────────────────────────────────────────────────────
interface PageHeaderProps {
  title: string;
  /** 오른쪽 슬롯 (미전달 시 기본 프로필 버튼) */
  rightSlot?: ReactNode;
  /** 왼쪽 슬롯 (미전달 시 기본 사이드바 버튼) */
  leftSlot?: ReactNode;
}
function MenuButton() {
  return (
    <button
      type="button"
      aria-label="메뉴"
      className="flex h-12 w-12 items-center justify-center transition-opacity hover:opacity-70"
    >
      <Icon icon={Menu01Icon} size="sm" color="brand" strokeWidth={2} />
    </button>
  );
}

// function ProfileButton() {
//   return (
//     <button
//       type="button"
//       aria-label="프로필"
//       className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-subtle transition-opacity hover:opacity-70"
//     >
//       <Icon icon={UserIcon} size="sm" color="brand" />
//     </button>
//   );
// }

export default function PageHeader({ title, leftSlot, rightSlot }: PageHeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border-muted bg-[color-mix(in_srgb,var(--color-surface)_95%,transparent)] backdrop-blur-sm">
      <div className="mx-auto flex h-18 items-center justify-between px-4">
        <div className="flex w-12 items-center">
          {leftSlot ?? <MenuButton />}
        </div>
        <h1 className="flex-1 text-center text-lg font-medium leading-tight tracking-tight text-fg-strong">
          {title}
        </h1>
        <div className="flex w-12 items-center justify-end">
          {rightSlot}
        </div>
      </div>
    </header>
  );
}
