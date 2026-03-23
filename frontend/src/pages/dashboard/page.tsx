import PageContainer from '~/components/common/page-container';

export default function DashboardPage() {
  return (
    <PageContainer>
      <div className="space-y-4">
        <div className="bg-card rounded-2xl border p-4">
          <div className="text-sm font-medium">환경 상태</div>
          <div className="text-muted-foreground mt-2 text-sm">placeholder</div>
        </div>

        <div className="bg-card rounded-2xl border p-4">
          <div className="text-sm font-medium">로봇 상태</div>
          <div className="text-muted-foreground mt-2 text-sm">placeholder</div>
        </div>

        <div className="bg-card rounded-2xl border p-4">
          <div className="text-sm font-medium">빠른 동작</div>
          <div className="text-muted-foreground mt-2 text-sm">placeholder</div>
        </div>
      </div>
    </PageContainer>
  );
}
