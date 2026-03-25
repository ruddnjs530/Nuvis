import {
  Calendar03Icon,
  Home01Icon,
  RobotIcon,
  ZapIcon,
} from '@hugeicons/core-free-icons';
import { Link, useLocation } from 'react-router';
import Icon from '~/components/common/icon';
import { cn } from '~/lib/utils';

// ── Data ──────────────────────────────────────────────────────────────────────
const items = [
  { to: '/', label: '홈', icon: Home01Icon },
  { to: '/control', label: '제어', icon: RobotIcon },
  { to: '/events', label: '이벤트', icon: ZapIcon },
  { to: '/schedules', label: '스케줄', icon: Calendar03Icon },
];

function isActive(pathname: string, to: string) {
  if (to === '/')
    return pathname === '/';
  return pathname.startsWith(to);
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function BottomNav() {
  const location = useLocation();

  return (
    // height: --h-bottom-nav(83px) = pt-3(12px) + nav-item(46px) + pb-6(24px)
    // border: --color-border-muted / bg: surface + /90 + backdrop-blur-sm
    <nav className="fixed bottom-0 left-1/2 z-50 w-full -translate-x-1/2 border-t border-border-muted bg-[color-mix(in_srgb,var(--color-surface)_90%,transparent)] backdrop-blur-md transition-all">
      {/* max-w: --layout-max-w(448px) / h: --h-bottom-nav */}
      <ul className="mx-auto grid max-w-[448px] grid-cols-4 px-4 pt-3 pb-6">
        {items.map((item) => {
          const active = isActive(location.pathname, item.to);

          return (
            <li key={item.to}>
              <Link
                to={item.to}
                // h: --h-nav-item(46px) / gap: --space-1(4px)
                // active: --color-brand / inactive: --color-fg-subtle
                className={cn(
                  'flex h-[46px] flex-col items-center justify-center gap-1 text-xs transition-colors',
                  active ? 'text-brand' : 'text-fg-subtle',
                )}
              >
                <Icon
                  icon={item.icon}
                  size="md"
                  strokeWidth={active ? 2 : 1.5}
                />
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
