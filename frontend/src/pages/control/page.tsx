import PageContainer from '~/components/common/page-container';

export default function ControlPage() {
  return (
    <PageContainer>
      <div className="space-y-4">
        <div className="bg-card rounded-2xl border p-4">
          <div className="text-sm font-medium">카메라</div>
          <div className="bg-muted mt-3 h-56 rounded-xl" />
        </div>

        <div className="bg-card rounded-2xl border p-4">
          <div className="text-sm font-medium">수동 제어</div>
          <div className="text-muted-foreground mt-2 text-sm">placeholder</div>
        </div>
      </div>
    </PageContainer>
  );
}
