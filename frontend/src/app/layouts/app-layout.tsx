import { Outlet, useLocation } from 'react-router';

import PageHeader from '~/components/common/page-header';
import BottomNav from '~/components/navigation/bottom-nav';

const titles: Record<string, string> = {
  '/': '대시보드',
  '/control': '실시간 제어',
  '/events': '이벤트',
  '/schedules': '스케줄',
};

export default function AppLayout() {
  const location = useLocation();

  const title = titles[location.pathname] ?? 'Home IoT';

  return (
    <div className="bg-muted/30 min-h-dvh">
      <div className="bg-background mx-auto flex min-h-dvh max-w-md flex-col">
        <PageHeader title={title} />

        <main className="flex min-h-0 flex-1 flex-col pb-28">
          <Outlet />
        </main>

        <BottomNav />
      </div>
    </div>
  );
}
