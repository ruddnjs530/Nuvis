import type { ReactNode } from 'react';

interface PageContainerProps {
  children: ReactNode;
}

export default function PageContainer({ children }: PageContainerProps) {
  return (
    <div className="mx-auto flex w-full max-w-md flex-1 flex-col px-4 py-4">
      {children}
    </div>
  );
}
