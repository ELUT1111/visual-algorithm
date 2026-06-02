const fs = require('fs');
const { test, expect } = require('@playwright/test');

test('shows algorithm overview and filters by learning path', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('#algorithm-overview')).toContainText('Total');
  await expect(page.locator('#algorithm-overview')).toContainText('53');
  await expect(page.locator('#learning-paths')).toContainText('DP Foundations');

  await page.locator('.learning-path', { hasText: 'DP Foundations' }).click();

  await expect(page.locator('.learning-path.active')).toContainText('DP Foundations');
  await expect(page.locator('.algo-card[data-key="dp/word_break"]')).toBeVisible();
  await expect(page.locator('.algo-card[data-key="dp/subset_sum"]')).toBeVisible();
  await expect(page.locator('.algo-card[data-key="graph/dijkstra"]')).toHaveCount(0);

  await page.locator('#algorithm-search').fill('word');
  await expect(page.locator('.algo-card[data-key="dp/word_break"]')).toBeVisible();
  await expect(page.locator('.algo-card[data-key="dp/subset_sum"]')).toHaveCount(0);

  await page.locator('.learning-path', { hasText: /^All/ }).click();
  await page.locator('#btn-clear-algo-search').click();
  await expect(page.locator('.algo-card[data-key="graph/dijkstra"]')).toBeVisible();
});

test('pins favorite algorithms and keeps recent selections', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => {
    localStorage.removeItem('val_favoriteAlgorithms');
    localStorage.removeItem('val_recentAlgorithms');
  });
  await page.reload();

  await expect(page.locator('#algorithm-quick-access')).toContainText('Star algorithms');

  const binarySearchCard = page.locator('.algo-card[data-key="array/binary_search"]');
  await binarySearchCard.locator('.algo-favorite').click();
  await expect(page.locator('#algorithm-quick-access')).toContainText('Favorites');
  await expect(page.locator('.quick-access-item[data-key="array/binary_search"]')).toBeVisible();

  await page.reload();
  await expect(page.locator('.quick-access-item[data-key="array/binary_search"]')).toBeVisible();

  await page.locator('.algo-card[data-key="graph/dijkstra"]').click();
  await expect(page.locator('#algorithm-quick-access')).toContainText('Recent');
  await expect(page.locator('.quick-access-item[data-key="graph/dijkstra"]')).toBeVisible();

  await page.locator('.quick-access-item[data-key="array/binary_search"]').click();
  await expect(page.locator('.algo-card[data-key="array/binary_search"]')).toHaveClass(/selected/);
  await expect(page.locator('#status-badge')).toContainText('binary_search');
});

test('loads, searches, runs an array algorithm, replays timeline, exports and imports run JSON', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('#algorithm-list .algo-card').first()).toBeVisible();
  await expect(page.locator('#status-badge')).not.toHaveText('Disconnected');

  await page.locator('#algorithm-search').fill('binary_search');
  const binarySearchCard = page.locator('.algo-card[data-key="array/binary_search"]');
  await expect(binarySearchCard).toBeVisible();
  await binarySearchCard.click();

  await expect(page.locator('.example-panel')).toBeVisible();
  await page.locator('.example-select').selectOption({ label: 'Found middle' });
  await page.getByRole('button', { name: 'Load' }).click();
  await expect(page.locator('#param-values')).toHaveValue('1,2,4,5,8,12,16');
  await expect(page.locator('#param-target')).toHaveValue('8');

  await page.getByRole('button', { name: /Random/ }).click();
  await expect(page.locator('#param-values')).not.toHaveValue('');
  await expect(page.locator('#param-target')).not.toHaveValue('');

  await page.locator('.example-select').selectOption({ label: 'Found middle' });
  await page.getByRole('button', { name: 'Load' }).click();

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#structure-container')).toBeVisible();
  await expect(page.locator('#run-summary')).toBeVisible();
  await expect(page.locator('#run-summary')).toContainText('Steps');
  await expect(page.locator('#run-summary')).toContainText('Messages');
  await expect(page.locator('#timeline-slider')).toBeEnabled();
  await expect(page.locator('#btn-export-run')).toBeEnabled();
  await expect(page.locator('#timeline-label')).toHaveText(/^\d+ \/ \d+$/);

  await page.locator('#btn-timeline-start').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^0 \/ \d+$/);
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^1 \/ \d+$/);

  const downloadPromise = page.waitForEvent('download');
  await page.locator('#btn-export-run').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain('array-binary_search-run');
  const exportedPath = await download.path();
  const exported = JSON.parse(fs.readFileSync(exportedPath, 'utf8'));
  expect(exported.run_metrics.step_count).toBeGreaterThan(0);
  expect(exported.run_metrics.message_count).toBeGreaterThan(0);

  await page.locator('#btn-reset').click();
  await expect(page.locator('#status-badge')).toHaveText('Ready');
  await expect(page.locator('#run-summary')).toBeHidden();

  const fileChooserPromise = page.waitForEvent('filechooser');
  await page.locator('#btn-import').click();
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles(exportedPath);

  await expect(page.locator('#status-badge')).toHaveText('Imported');
  await expect(page.locator('#param-values')).toHaveValue('1,2,4,5,8,12,16');
  await expect(page.locator('#param-target')).toHaveValue('8');
  await expect(page.locator('#timeline-slider')).toBeEnabled();
  await expect(page.locator('#timeline-label')).toHaveText(new RegExp(`^${exported.step_count} / ${exported.step_count}$`));
  await expect(page.locator('#run-summary')).toBeVisible();
  await expect(page.locator('#run-summary')).toContainText('Steps');
});

test('loads a graph-backed example and prepares its parameters', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('dijkstra');
  await page.locator('.algo-card[data-key="graph/dijkstra"]').click();
  await page.locator('.example-select').selectOption({ label: 'City distances' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#graph-container')).toBeVisible();
  await expect(page.locator('#param-source')).toHaveValue('A');
  await expect(page.locator('#status-badge')).toContainText('dijkstra');
});

test('runs a string matching algorithm and renders structured state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('rabin_karp');
  await page.locator('.algo-card[data-key="string/rabin_karp"]').click();
  await page.locator('.example-select').selectOption({ label: 'Rolling hash search' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-text')).toHaveValue('ababcabcabababd');
  await expect(page.locator('#param-pattern')).toHaveValue('ababd');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('pattern hash');
  await expect(page.locator('#state-content')).toContainText('matches');

  await page.locator('#btn-timeline-start').click();
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#state-content')).toContainText('window hash');
});

test('runs z algorithm and exposes the z table in the state panel', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('z_algorithm');
  await page.locator('.algo-card[data-key="string/z_algorithm"]').click();
  await page.locator('.example-select').selectOption({ label: 'Prefix overlap' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-text')).toHaveValue('aabxaabxcaabxaabxay');
  await expect(page.locator('#param-pattern')).toHaveValue('aabxa');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('z table');
  await expect(page.locator('#state-content')).toContainText('matches');

  await page.locator('#btn-timeline-start').click();
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#state-content')).toContainText('separator');
});

test('runs a max-flow example and shows residual-network state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('edmonds_karp');
  await page.locator('.algo-card[data-key="graph/edmonds_karp"]').click();
  await page.locator('.example-select').selectOption({ label: 'Capacity network' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-source')).toHaveValue('S');
  await expect(page.locator('#param-target')).toHaveValue('T');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('max flow');
  await expect(page.locator('#state-content')).toContainText('residual network');
  await expect(page.locator('#state-content')).toContainText('augmentations');

  await page.locator('#btn-timeline-start').click();
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#state-content')).toContainText('flow table');
});

test('compares max-flow algorithms on the same capacity network', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('edmonds_karp');
  await page.locator('.algo-card[data-key="graph/edmonds_karp"]').click();
  await page.locator('.example-select').selectOption({ label: 'Capacity network' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('.compare-panel')).toBeVisible();
  await page.getByRole('button', { name: 'Compare' }).click();

  await expect(page.locator('.compare-results')).toContainText('edmonds_karp');
  await expect(page.locator('.compare-results')).toContainText('dinic');
  await expect(page.locator('.compare-results')).toContainText('max flow: 19');
});

test('shows backend validation errors inside the parameter panel', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('edmonds_karp');
  await page.locator('.algo-card[data-key="graph/edmonds_karp"]').click();
  await page.locator('.example-select').selectOption({ label: 'Capacity network' });
  await page.getByRole('button', { name: 'Load' }).click();

  await page.locator('#param-target').selectOption('S');
  await page.locator('#btn-play').click();

  await expect(page.locator('.param-error-panel')).toBeVisible();
  await expect(page.locator('.param-error-panel')).toContainText('source and target');
  await expect(page.locator('.param-group[data-param-name="source"]')).toHaveClass(/error/);
  await expect(page.locator('.param-group[data-param-name="target"]')).toHaveClass(/error/);
});

test('runs a subset-sum example and shows DP backtracking state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('subset_sum');
  await page.locator('.algo-card[data-key="dp/subset_sum"]').click();
  await page.locator('.example-select').selectOption({ label: 'Reachable target' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('3,34,4,12,5,2');
  await expect(page.locator('#param-target')).toHaveValue('9');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('subset found');
  await expect(page.locator('#state-content')).toContainText('selected values');
  await expect(page.locator('#state-content')).toContainText('selected sum');
  await expect(page.locator('#state-content')).toContainText('backtrack path');
});

test('runs word break and shows segmentation state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('word_break');
  await page.locator('.algo-card[data-key="dp/word_break"]').click();
  await page.locator('.example-select').selectOption({ label: 'Multiple words' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-text')).toHaveValue('catsanddog');
  await expect(page.locator('#param-words')).toHaveValue('cat,cats,and,sand,dog');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('can segment');
  await expect(page.locator('#state-content')).toContainText('segmentation');
  await expect(page.locator('#state-content')).toContainText('dp table');
});

test('runs fenwick tree and shows prefix query state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('fenwick_tree');
  await page.locator('.algo-card[data-key="tree/fenwick_tree"]').click();
  await page.locator('.example-select').selectOption({ label: 'Prefix sum' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('1,7,3,0,7,8,3,2,6,2');
  await expect(page.locator('#param-query_index')).toHaveValue('5');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('prefix sum');
  await expect(page.locator('#state-content')).toContainText('query path');
  await expect(page.locator('#state-content')).toContainText('tree');
});

test('runs manacher and shows palindrome radius state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('manacher');
  await page.locator('.algo-card[data-key="string/manacher"]').click();
  await page.locator('.example-select').selectOption({ label: 'Odd palindrome' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-text')).toHaveValue('babad');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('longest palindrome');
  await expect(page.locator('#state-content')).toContainText('radii table');
  await expect(page.locator('#state-content')).toContainText('length');
});
