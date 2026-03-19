import { useQuery } from '@tanstack/react-query';
import { api } from '~/lib/api/client';

function useDummyData() {
  return useQuery({
    queryKey: ['room-data'],
    queryFn: () => {
      return api({
        // method: 'get',
        url: 'health-check',
        // type: 'text',
        // apiPrefix: 'api/v1',
        // options: {
        //   json: {
        //     key: 'value',
        //   },
        // },
      });
    },
  });
}

export default function DashboardPage() {
  return (
    <div>
      <div>Dashboard</div>
      <p>{JSON.stringify(useDummyData().status)}</p>
    </div>
  );
}
