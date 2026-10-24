import assert from 'node:assert/strict';
import { assessNotifications } from './creative_preview_observations.mjs';

const expectedPath = '/events/fetch-get';
const expectedMethod = 'GET';
const cases = [
  {id:'empty-isolated-log', isolated:true, observations:[], expected:true},
  {id:'expected-event-is-still-forbidden', isolated:true, observations:[{method:'GET',path:expectedPath}], expected:false},
  {id:'unexpected-event-path-is-forbidden', isolated:true, observations:[{method:'GET',path:'/events/unexpected-audit-canary'}], expected:false},
  {id:'unexpected-event-method-is-forbidden', isolated:true, observations:[{method:'HEAD',path:'/events/unexpected'}], expected:false},
  {id:'mixed-events-are-all-preserved', isolated:true, observations:[{method:'GET',path:expectedPath},{method:'POST',path:'/events/other'}], expected:false},
  {id:'control-must-reach-trap', isolated:false, observations:[], expected:false},
  {id:'expected-control-event', isolated:false, observations:[{method:'GET',path:expectedPath}], expected:true},
  {id:'wrong-control-path', isolated:false, observations:[{method:'GET',path:'/events/other'}], expected:false},
  {id:'wrong-control-method', isolated:false, observations:[{method:'HEAD',path:expectedPath}], expected:false},
  {id:'control-with-extra-notification', isolated:false, observations:[{method:'GET',path:expectedPath},{method:'GET',path:'/events/other'}], expected:false},
];
const results = cases.map(vector => {
  const result = assessNotifications(vector.observations, {isolated:vector.isolated, expectedPath, expectedMethod});
  // The receipt must retain the complete observations, even when they fail.
  assert.deepEqual(result.notifications, vector.observations);
  assert.notEqual(result.notifications, vector.observations);
  return {id:vector.id, passed:result.passed === vector.expected, expected_check_result:vector.expected, actual:result};
});
const report = {profile:'preview-notification-assertions-1', passed:results.filter(x=>x.passed).length, total:results.length, cases:results};
if(process.argv.includes('--json')) console.log(JSON.stringify(report,null,2));
else {for(const item of results) console.log((item.passed?'PASS ':'FAIL ')+item.id);console.log(`${report.passed}/${report.total} notification assertions pass`);}
if(report.passed !== report.total) process.exitCode=1;
