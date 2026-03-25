import { Outlet } from 'react-router';

export default function AuthLayout() {
  return (
    <div className="bg-muted/30 min-h-dvh">
      <div className="bg-background mx-auto flex min-h-dvh max-w-md flex-col">
        <main className="flex flex-1 flex-col justify-center px-4 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
