import type { ReactNode } from 'react';
import { ArrowUpRightIcon } from '@hugeicons/core-free-icons';
import { Link } from 'react-router';

import Icon from '~/components/common/icon';

interface SectionLinkFooterProps {
  to: string;
  children: ReactNode;
}

/** 섹션 하단 우측 링크 배열 */
export default function SectionLinkFooter({ to, children }: SectionLinkFooterProps) {
  return (
    <div className="mt-3 flex justify-end">
      <Link to={to} className="flex items-center gap-1 text-sm text-brand">
        {children}
        <Icon icon={ArrowUpRightIcon} size="sm" />
      </Link>
    </div>
  );
}
