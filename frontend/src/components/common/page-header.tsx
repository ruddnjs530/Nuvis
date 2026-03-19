import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  rightSlot?: ReactNode;
}

export default function PageHeader({ title, rightSlot }: PageHeaderProps) {
  return (
    <header className="bg-background/95 supports-[backdrop-filter]:bg-background/80 sticky top-0 z-20 border-b backdrop-blur">
      <div className="mx-auto flex h-14 max-w-md items-center justify-between px-4">
        <h1 className="text-base font-semibold">{title}</h1>
        <div className="flex items-center">{rightSlot}</div>
      </div>
    </header>
  );
}
