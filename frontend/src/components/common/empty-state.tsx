interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}

export default function EmptyState({ title = '등록된 데이터가 없습니다.', description, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 p-10 text-center">
      {icon
        ? (
            <div className="mb-2 text-fg-muted/50">{icon}</div>
          )
        : (
            <div className="mb-2 h-16 w-16 rounded-full bg-surface-sunken" />
          )}
      <h3 className="text-base font-bold text-fg-strong">{title}</h3>
      {description && <p className="text-sm text-fg-muted">{description}</p>}
    </div>
  );
}
