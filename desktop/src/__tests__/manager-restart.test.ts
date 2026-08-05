import { EventEmitter } from 'events';

const mockNotificationShow = jest.fn();

jest.mock('electron', () => ({
  app: { isPackaged: false, getPath: () => '/tmp' },
  Notification: jest.fn(() => ({ show: mockNotificationShow })),
}));
jest.mock('electron-log', () => ({
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
}));

import { ServiceManager } from '../main/services/manager';

test('restart storm notifies the user and retries after the crash window', () => {
  jest.useFakeTimers();
  jest.setSystemTime(1_000_000);
  const manager = new ServiceManager();
  const service = {
    process: null,
    status: 'stopped',
    crashTimestamps: [],
    restartTimer: null,
    config: {
      id: 'sensing',
      command: 'python',
      restartOnCrash: true,
      maxRestartsInWindow: 3,
      restartWindowMs: 60_000,
      initialRestartDelayMs: 1,
    },
  };
  (manager as any).services.set('sensing', service);
  const children: EventEmitter[] = [];
  jest.spyOn(manager, 'spawnAndRegister').mockImplementation(() => {
    const child = new EventEmitter();
    (child as any).stdout = null;
    (child as any).stderr = null;
    service.process = child as any;
    child.on('exit', () => {
      service.process = null;
    });
    children.push(child);
    return child as any;
  });

  manager.startService('sensing');
  children[0].emit('exit', 1);
  jest.advanceTimersByTime(1);
  children[1].emit('exit', 1);
  jest.advanceTimersByTime(2);
  children[2].emit('exit', 1);

  expect(mockNotificationShow).toHaveBeenCalledTimes(1);
  expect(service.status).toBe('error');
  jest.advanceTimersByTime(60_000);
  expect(children).toHaveLength(4);
  expect(service.status).toBe('running');
  jest.useRealTimers();
});
