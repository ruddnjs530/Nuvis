import { Outlet } from 'react-router';

export default function AppLayout() {
  return (
    <div>
      <h1>Auth Layout</h1>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
