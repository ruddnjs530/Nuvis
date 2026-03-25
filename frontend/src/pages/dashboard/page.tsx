import {
  EnvironmentSummarySection,
  QuickActionSection,
  RobotStatusSection,
} from './components';

export default function DashboardPage() {
  return (
    <div className="space-y-5 py-5">
      <EnvironmentSummarySection />
      <RobotStatusSection />
      <QuickActionSection />
    </div>
  );
}
