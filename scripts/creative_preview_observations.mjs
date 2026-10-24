// Shared assertion for the synthetic notification trap, not an egress filter.
export function assessNotifications(observations, {isolated, expectedPath, expectedMethod}) {
  const notifications = observations.map(observation => ({...observation}));
  const expected = observation => observation.path === expectedPath && observation.method === expectedMethod;
  return {
    passed: isolated ? notifications.length === 0 : notifications.length > 0 && notifications.every(expected),
    notifications,
  };
}
