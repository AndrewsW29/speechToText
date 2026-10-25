// Collection-level assertions: they run after every request in the collection.
pm.test('X-Correlation-ID header is returned', () => {
  pm.expect(pm.response.headers.has('X-Correlation-ID')).to.be.true;
});

pm.test('response time is within the latency budget', () => {
  const budget = Number(pm.variables.get('latencyBudgetMs') || 5000);
  pm.expect(pm.response.responseTime).to.be.below(budget);
});

if (pm.response.code >= 400) {
  pm.test('errors are RFC 9457 problem details without internals', () => {
    pm.expect(pm.response.headers.get('Content-Type')).to.include('application/problem+json');
    const body = pm.response.json();
    pm.expect(body).to.include.all.keys('type', 'title', 'status');
    pm.expect(body.status).to.equal(pm.response.code);
    pm.expect(JSON.stringify(body)).to.not.match(/Traceback|SELECT |at \w+\.\w+\(/);
  });
}
