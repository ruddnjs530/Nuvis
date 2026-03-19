import PageContainer from '~/components/common/page-container';

export default function SchedulesPage() {
  return (
    <PageContainer>
      <div className="space-y-3">
        {[1, 2].map(i => (
          <div key={i} className="bg-card rounded-2xl border p-4">
            <div className="text-sm font-medium">
              스케줄 #
              {i}
            </div>
            <div className="text-muted-foreground mt-2 text-sm">placeholder</div>
          </div>
        ))}
      </div>
    </PageContainer>
  );
}
