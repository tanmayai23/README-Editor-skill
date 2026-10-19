import { greet } from './lib';
import { format } from '@lib/format';
export const App = () => greet(format('x'));
