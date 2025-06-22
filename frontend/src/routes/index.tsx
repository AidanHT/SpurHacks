import { RouteObject } from 'react-router-dom';
import Splash from '@/pages/Splash';
import AppLayout from '@/layouts/AppLayout';
import NewSession from '@/pages/NewSession';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Splash />,
  },
  {
    path: '/app',
    element: <AppLayout />,
  },
  {
    path: '/new',
    element: <NewSession />,
  },
];

export default routes; 