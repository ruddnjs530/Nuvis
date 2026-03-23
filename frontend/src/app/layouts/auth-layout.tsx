import { Outlet } from 'react-router';

export default function AuthLayout() {
  return (
    <div className="bg-muted/30 min-h-dvh">
      <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-4">
        <Outlet />
      </main>
    </div>
  );
}
