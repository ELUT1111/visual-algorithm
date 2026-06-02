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

test('filters algorithms by tag and recommends related algorithms', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('#algorithm-tags')).toContainText('Shortest Path');
  await page.locator('.algorithm-tag[data-tag="shortest-path"]').click();

  await expect(page.locator('.algorithm-tag.active')).toContainText('Shortest Path');
  await expect(page.locator('.algo-card[data-key="graph/dijkstra"]')).toBeVisible();
  await expect(page.locator('.algo-card[data-key="array/bubble_sort"]')).toHaveCount(0);

  await page.locator('.algo-card[data-key="graph/dijkstra"]').click();
  await expect(page.locator('#edu-next')).toContainText('bellman_ford');
  await expect(page.locator('.edu-next-item[data-key="graph/bellman_ford"]')).toBeVisible();

  await page.locator('.edu-next-item[data-key="graph/bellman_ford"]').click();
  await expect(page.locator('.algo-card[data-key="graph/bellman_ford"]')).toHaveClass(/selected/);
  await expect(page.locator('#status-badge')).toContainText('bellman_ford');
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
  await expect(page.locator('#run-summary')).toContainText('Position');
  await expect(page.locator('#run-summary')).toContainText('Phases');
  await expect(page.locator('#run-summary')).toContainText('Actions');
  await expect(page.locator('#step-detail')).toBeVisible();
  await expect(page.locator('#step-detail')).toContainText('Step');
  await expect(page.locator('#step-detail')).toContainText('Phase');
  await expect(page.locator('#step-detail')).toContainText('Action');
  await page.locator('[data-panel-toggle="run-summary"]').click();
  await expect(page.locator('#run-summary')).toHaveClass(/is-collapsed/);
  await expect(page.locator('#run-summary-content')).toBeHidden();
  await page.locator('[data-panel-toggle="run-summary"]').click();
  await expect(page.locator('#run-summary')).not.toHaveClass(/is-collapsed/);
  await page.locator('[data-panel-toggle="step-detail"]').click();
  await expect(page.locator('#step-detail-content')).toBeHidden();
  await page.locator('[data-panel-toggle="step-detail"]').click();
  await page.locator('[data-panel-toggle="step-log"]').click();
  await expect(page.locator('#step-log')).toHaveClass(/is-collapsed/);
  await expect(page.locator('#step-log-content')).toBeHidden();
  await page.locator('[data-panel-toggle="step-log"]').click();
  await expect(page.locator('#step-log')).not.toHaveClass(/is-collapsed/);
  await expect(page.locator('#timeline-slider')).toBeEnabled();
  await expect(page.locator('#btn-export-run')).toBeEnabled();
  await expect(page.locator('#timeline-label')).toHaveText(/^\d+ \/ \d+$/);
  await expect(page.locator('#log-match-count')).toContainText(/\d+ steps/);
  await page.locator('#log-search').fill('8');
  await expect(page.locator('#log-match-count')).toContainText(/\/ \d+ steps/);
  await expect(page.locator('#step-log-content .log-entry').filter({ hasText: '8' }).first()).toBeVisible();
  await page.locator('#btn-clear-log-filter').click();
  await page.locator('#log-phase-filter').selectOption('result');
  await expect(page.locator('#step-log-content .log-entry:visible').first()).toContainText('result');
  await page.locator('#btn-clear-log-filter').click();
  await expect(page.locator('#log-search')).toHaveValue('');
  await expect(page.locator('#log-phase-filter')).toHaveValue('all');

  await page.locator('#btn-timeline-start').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^0 \/ \d+$/);
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^1 \/ \d+$/);
  await expect(page.locator('#step-detail')).toContainText(/1 \/ \d+/);
  const targetLog = page.locator('#step-log-content .log-entry[data-step-index="2"]').first();
  await targetLog.click();
  await expect(page.locator('#timeline-label')).toHaveText(/^3 \/ \d+$/);
  await expect(page.locator('#step-detail')).toContainText(/3 \/ \d+/);
  await expect(targetLog).toHaveClass(/active/);
  await page.locator('#btn-bookmark-toggle').click();
  await expect(page.locator('#btn-bookmark-toggle')).toHaveClass(/active/);
  await page.locator('#btn-timeline-start').click();
  await page.locator('#btn-bookmark-next').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^3 \/ \d+$/);
  await page.locator('#btn-timeline-start').click();
  await page.locator('#timeline-bookmark-steps').check();
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^3 \/ \d+$/);

  const downloadPromise = page.waitForEvent('download');
  await page.locator('#btn-export-run').click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain('array-binary_search-run');
  const exportedPath = await download.path();
  const exported = JSON.parse(fs.readFileSync(exportedPath, 'utf8'));
  expect(exported.run_metrics.step_count).toBeGreaterThan(0);
  expect(exported.run_metrics.message_count).toBeGreaterThan(0);
  expect(exported.bookmarks).toEqual([3]);

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
  await expect(page.locator('#run-summary')).toContainText('Position');
  await expect(page.locator('#run-summary')).toContainText(`${exported.step_count} / ${exported.step_count}`);
  await expect(page.locator('#run-summary')).toContainText('Phases');
  await expect(page.locator('#run-summary')).toContainText('Actions');
  await expect(page.locator('#step-detail')).toBeVisible();
  await expect(page.locator('#step-detail')).toContainText(`${exported.step_count} / ${exported.step_count}`);
  await page.locator('#btn-timeline-start').click();
  await page.locator('#btn-bookmark-next').click();
  await expect(page.locator('#timeline-label')).toHaveText(/^3 \/ \d+$/);
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

test('keeps graph layout stable when scrubbing the timeline slider', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('dijkstra');
  await page.locator('.algo-card[data-key="graph/dijkstra"]').click();
  await page.locator('.example-select').selectOption({ label: 'City distances' });
  await page.getByRole('button', { name: 'Load' }).click();

  const expectedViewport = await page.evaluate(() => {
    window.app.graphEditor.network.moveTo({
      position: { x: 40, y: -30 },
      scale: 0.78,
      animation: false
    });
    return window.app.graphEditor.getViewport();
  });

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();
  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#timeline-slider')).toBeEnabled();
  await expect(page.locator('#timeline-key-steps')).toBeEnabled();

  const before = await page.evaluate(() => {
    const positions = Object.values(window.app.graphEditor.network.getPositions());
    const xs = positions.map(pos => pos.x);
    const ys = positions.map(pos => pos.y);
    return {
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys)
    };
  });

  const total = await page.locator('#timeline-slider').evaluate(slider => Number(slider.max));
  const sliderBox = await page.locator('#timeline-slider').boundingBox();
  expect(sliderBox).not.toBeNull();
  await page.mouse.move(sliderBox.x + sliderBox.width * 0.35, sliderBox.y + sliderBox.height / 2);
  await expect(page.locator('#timeline-preview')).toHaveClass(/visible/);
  await expect(page.locator('#timeline-preview')).toContainText(/\d+ \/ \d+/);
  await page.mouse.click(sliderBox.x + sliderBox.width * 0.2, sliderBox.y + sliderBox.height / 2);
  await expect.poll(async () => page.locator('#timeline-label').textContent()).not.toBe(`${total} / ${total}`);
  const scrubbedLabel = await page.locator('#timeline-label').textContent();

  await page.locator('#timeline-key-steps').check();
  await page.keyboard.press('ArrowRight');
  await expect.poll(async () => page.locator('#timeline-label').textContent()).not.toBe(scrubbedLabel);
  await page.keyboard.press('ArrowLeft');
  await expect(page.locator('#status-badge')).toHaveText(/Replaying|Replay End/);
  await expect.poll(async () => page.evaluate(() => window.app.graphEditor.getViewport())).toMatchObject({
    scale: expect.closeTo(expectedViewport.scale, 2)
  });

  const after = await page.evaluate(() => {
    const positions = Object.values(window.app.graphEditor.network.getPositions());
    const xs = positions.map(pos => pos.x);
    const ys = positions.map(pos => pos.y);
    const viewport = window.app.graphEditor.getViewport();
    return {
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
      viewport,
      layoutLocked: window.app.graphEditor.isLayoutLocked()
    };
  });

  expect(before.width).toBeGreaterThan(100);
  expect(before.height).toBeGreaterThan(100);
  expect(after.width).toBeGreaterThan(100);
  expect(after.height).toBeGreaterThan(100);
  expect(after.viewport.x).toBeCloseTo(expectedViewport.x, 0);
  expect(after.viewport.y).toBeCloseTo(expectedViewport.y, 0);
  expect(after.viewport.scale).toBeCloseTo(expectedViewport.scale, 2);
  expect(after.layoutLocked).toBe(true);
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
  await expect(page.locator('.state-flow-table').first()).toBeVisible();

  await page.locator('#btn-timeline-start').click();
  await page.locator('#btn-timeline-next').click();
  await expect(page.locator('#state-content')).toContainText('flow table');

  for (let i = 0; i < 8 && await page.locator('.state-section.changed').count() === 0; i++) {
    await page.locator('#btn-timeline-next').click();
  }
  await expect(page.locator('.state-section.changed').first()).toBeVisible();
  await expect(page.locator('#state-diff-summary')).toContainText('Changed:');
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
  await expect(page.locator('.compare-results')).toContainText('Duration');
  await expect(page.locator('.compare-results')).toContainText('Phases');
  await expect(page.locator('.compare-results')).toContainText('Actions');
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
  await expect(page.locator('.state-dp-table')).toHaveCount(1);
  await expect(page.locator('.state-cell-true').first()).toBeVisible();
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
