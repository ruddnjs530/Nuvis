import {
  Calendar03Icon,
  Home01Icon,
  RobotIcon,
  ZapIcon,
} from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';
import { Link, useLocation } from 'react-router';
import { cn } from '~/lib/utils';

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

export default function BottomNav() {
  const location = useLocation();

  return (
    <nav className="border-border bg-background/95 sticky bottom-0 z-20 border-t backdrop-blur">
      <ul className="mx-auto grid h-16 max-w-md grid-cols-4">
        {items.map((item) => {
          const active = isActive(location.pathname, item.to);
          const icon = item.icon;

          return (
            <li key={item.to}>
              <Link
                to={item.to}
                className={cn(
                  'flex h-full flex-col items-center justify-center gap-1 text-xs',
                  active ? 'text-foreground' : 'text-muted-foreground',
                )}
              >
                <HugeiconsIcon icon={icon} size={20} strokeWidth={1.8} />
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
