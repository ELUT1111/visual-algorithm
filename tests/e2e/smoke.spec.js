const fs = require('fs');
const { test, expect } = require('@playwright/test');

test('shows algorithm overview and filters by learning path', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('#algorithm-overview')).toContainText('Total');
  await expect(page.locator('#algorithm-overview')).toContainText('66');
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
  await page.addInitScript(() => {
    localStorage.removeItem('val_savedRunRecords');
  });
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

  const logDownloadPromise = page.waitForEvent('download');
  await page.locator('#btn-export-log').click();
  const logDownload = await logDownloadPromise;
  expect(logDownload.suggestedFilename()).toContain('log');
  const logPath = await logDownload.path();
  const exportedLog = fs.readFileSync(logPath, 'utf8');
  expect(exportedLog).toContain('[');

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

  await expect(page.locator('#btn-save-run')).toBeEnabled();
  await page.locator('#btn-save-run').click();
  await expect(page.locator('#run-history-list .run-history-item')).toBeVisible();
  await expect(page.locator('#run-history-list')).toContainText('array/binary search');

  await page.locator('#btn-reset').click();
  await expect(page.locator('#status-badge')).toHaveText('Ready');
  await expect(page.locator('#run-summary')).toBeHidden();
  await expect(page.locator('#btn-save-run')).toBeDisabled();

  await page.locator('#run-history-list .run-history-load').first().click();
  await expect(page.locator('#status-badge')).toHaveText('Imported');
  await expect(page.locator('#param-values')).toHaveValue('1,2,4,5,8,12,16');
  await expect(page.locator('#param-target')).toHaveValue('8');
  await expect(page.locator('#timeline-slider')).toBeEnabled();

  await page.locator('#btn-reset').click();

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
  await expect(page.locator('.state-diff-detail')).toBeVisible();
  await expect(page.locator('.state-diff-detail')).toContainText('Before:');
  await expect(page.locator('.state-diff-detail')).toContainText('After:');
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

test('runs sparse table and shows O(1) range query state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('sparse_table');
  await page.locator('.algo-card[data-key="array/sparse_table"]').click();
  await page.locator('.example-select').selectOption({ label: 'Range minimum' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('7,2,3,0,5,10,3,12,18');
  await expect(page.locator('#param-query_left')).toHaveValue('1');
  await expect(page.locator('#param-query_right')).toHaveValue('6');
  await expect(page.locator('#param-operation')).toHaveValue('min');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('sparse table');
  await expect(page.locator('#state-content')).toContainText('log table');
  await expect(page.locator('#state-content')).toContainText('query blocks');
  await expect(page.locator('#state-content')).toContainText('query result');
});

test('runs segment tree and shows range query state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('segment_tree');
  await page.locator('.algo-card[data-key="tree/segment_tree"]').click();
  await page.locator('.example-select').selectOption({ label: 'Range sum' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('2,1,5,3,4,7');
  await expect(page.locator('#param-query_left')).toHaveValue('1');
  await expect(page.locator('#param-query_right')).toHaveValue('4');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('range sum');
  await expect(page.locator('#state-content')).toContainText('accepted nodes');
  await expect(page.locator('#state-content')).toContainText('query range');
});

test('runs lca and shows ancestor table state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('lca');
  await page.locator('.algo-card[data-key="tree/lca"]').click();
  await page.locator('.example-select').selectOption({ label: 'Sibling leaves' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-source')).toHaveValue('A');
  await expect(page.locator('#param-node_a')).toHaveValue('D');
  await expect(page.locator('#param-node_b')).toHaveValue('E');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('lca');
  await expect(page.locator('#state-content')).toContainText('ancestor table');
  await expect(page.locator('#state-content')).toContainText('lca path');
  await expect(page.locator('#state-content')).toContainText('lift trace');
});

test('runs heavy-light decomposition and shows path segments', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('heavy_light');
  await page.locator('.algo-card[data-key="tree/heavy_light_decomposition"]').click();
  await page.locator('.example-select').selectOption({ label: 'Path sum' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-source')).toHaveValue('A');
  await expect(page.locator('#param-node_a')).toHaveValue('D');
  await expect(page.locator('#param-node_b')).toHaveValue('G');
  await expect(page.locator('#param-values')).toHaveValue('1,2,3,4,5,6,7');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('heavy child');
  await expect(page.locator('#state-content')).toContainText('path segments');
  await expect(page.locator('#state-content')).toContainText('path query result');
  await expect(page.locator('#state-content')).toContainText('base array');
});

test('runs trie deletion and shows prefix-count state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('trie');
  await page.locator('.algo-card[data-key="tree/trie"]').click();
  await page.locator('.example-select').selectOption({ label: 'Delete and count' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-words')).toHaveValue('app,apple,apt,bat');
  await expect(page.locator('#param-query_prefix')).toHaveValue('ap');
  await expect(page.locator('#param-delete_words')).toHaveValue('app');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('prefix query result');
  await expect(page.locator('#state-content')).toContainText('word frequency');
  await expect(page.locator('#state-content')).toContainText('deleted words');
  await expect(page.locator('#state-content')).toContainText('deletion results');
});

test('runs aho-corasick and shows failure-link state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('aho_corasick');
  await page.locator('.algo-card[data-key="tree/aho_corasick"]').click();
  await page.locator('.example-select').selectOption({ label: 'Classic multi-match' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-patterns')).toHaveValue('he,she,his,hers');
  await expect(page.locator('#param-text')).toHaveValue('ushers');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('failure links');
  await expect(page.locator('#state-content')).toContainText('output table');
  await expect(page.locator('#state-content')).toContainText('scan trace');
  await expect(page.locator('#state-content')).toContainText('match count');
});

test('runs avl deletion and shows rebalancing state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('avl');
  await page.locator('.algo-card[data-key="tree/avl"]').click();
  await page.locator('.example-select').selectOption({ label: 'Delete and rebalance' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('20,10,30,5,15,25,40,2,7');
  await expect(page.locator('#param-delete_values')).toHaveValue('30,10');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('deleted values');
  await expect(page.locator('#state-content')).toContainText('inorder');
  await expect(page.locator('#state-content')).toContainText('tree');
});

test('runs red-black deletion and shows fix-up state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('red_black');
  await page.locator('.algo-card[data-key="tree/red_black"]').click();
  await page.locator('.example-select').selectOption({ label: 'Delete fix-up' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('20,10,30,5,15,25,40,1,7');
  await expect(page.locator('#param-delete_values')).toHaveValue('5,30');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('deleted values');
  await expect(page.locator('#state-content')).toContainText('root color');
  await expect(page.locator('#state-content')).toContainText('black height valid');
});

test('runs treap and shows rotation state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('treap');
  await page.locator('.algo-card[data-key="tree/treap"]').click();
  await page.locator('.example-select').selectOption({ label: 'Priority rotations' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-values')).toHaveValue('50,30,70,20,40,60,80');
  await expect(page.locator('#param-priorities')).toHaveValue('50,30,40,10,35,20,60');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('heap valid');
  await expect(page.locator('#state-content')).toContainText('rotations');
  await expect(page.locator('#state-content')).toContainText('inorder');
});

test('runs dag longest path and shows critical path state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('dag_longest_path');
  await page.locator('.algo-card[data-key="graph/dag_longest_path"]').click();
  await page.locator('.example-select').selectOption({ label: 'Critical path' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-source')).toHaveValue('S');
  await expect(page.locator('#param-target')).toHaveValue('T');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('critical path');
  await expect(page.locator('#state-content')).toContainText('longest distance');
  await expect(page.locator('#state-content')).toContainText('topological order');
});

test('runs euler path and shows edge-covering trail state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('euler_path');
  await page.locator('.algo-card[data-key="graph/euler_path"]').click();
  await page.locator('.example-select').selectOption({ label: 'Euler trail' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-start')).toHaveValue('A');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('euler path');
  await expect(page.locator('#state-content')).toContainText('euler edges');
  await expect(page.locator('#state-content')).toContainText('used edge count');
  await expect(page.locator('#state-content')).toContainText('edge count');
});

test('runs kruskal and shows union-find optimization state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('kruskal');
  await page.locator('.algo-card[data-key="graph/kruskal"]').click();
  await page.locator('.example-select').selectOption({ label: 'City MST' });
  await page.getByRole('button', { name: 'Load' }).click();

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('find traces');
  await expect(page.locator('#state-content')).toContainText('compression updates');
  await expect(page.locator('#state-content')).toContainText('union trace');
  await expect(page.locator('#state-content')).toContainText('rank updates');
});

test('runs bridges articulation and shows biconnected components', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('bridges_articulation');
  await page.locator('.algo-card[data-key="graph/bridges_articulation"]').click();
  await page.locator('.example-select').selectOption({ label: 'Chain bridges' });
  await page.getByRole('button', { name: 'Load' }).click();

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('bridges');
  await expect(page.locator('#state-content')).toContainText('articulation points');
  await expect(page.locator('#state-content')).toContainText('biconnected components');
  await expect(page.locator('#state-content')).toContainText('component trace');
});

test('runs hopcroft-karp and shows matching state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('hopcroft_karp');
  await page.locator('.algo-card[data-key="graph/hopcroft_karp"]').click();
  await page.locator('.example-select').selectOption({ label: 'Worker-task matching' });
  await page.getByRole('button', { name: 'Load' }).click();

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('matching size');
  await expect(page.locator('#state-content')).toContainText('left partition');
  await expect(page.locator('#state-content')).toContainText('right partition');
});

test('runs stoer-wagner and shows global min-cut state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('stoer_wagner');
  await page.locator('.algo-card[data-key="graph/stoer_wagner"]').click();
  await page.locator('.example-select').selectOption({ label: 'Global min cut' });
  await page.getByRole('button', { name: 'Load' }).click();

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('best cut value');
  await expect(page.locator('#state-content')).toContainText('min cut edges');
  await expect(page.locator('#state-content')).toContainText('phase cuts');
  await expect(page.locator('#state-content')).toContainText('contractions');
});

test('runs push-relabel and shows preflow state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('push_relabel');
  await page.locator('.algo-card[data-key="graph/push_relabel"]').click();
  await page.locator('.example-select').selectOption({ label: 'Preflow network' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-source')).toHaveValue('S');
  await expect(page.locator('#param-target')).toHaveValue('T');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('max flow');
  await expect(page.locator('#state-content')).toContainText('heights');
  await expect(page.locator('#state-content')).toContainText('excess');
  await expect(page.locator('#state-content')).toContainText('push trace');
  await expect(page.locator('#state-content')).toContainText('relabel trace');
});

test('runs min-cost max-flow and shows cost state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('min_cost_max_flow');
  await page.locator('.algo-card[data-key="graph/min_cost_max_flow"]').click();
  await page.locator('.example-select').selectOption({ label: 'Costed network' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-source')).toHaveValue('S');
  await expect(page.locator('#param-target')).toHaveValue('T');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('max flow');
  await expect(page.locator('#state-content')).toContainText('min cost');
  await expect(page.locator('#state-content')).toContainText('flow table');
});

test('runs hungarian assignment and shows minimum cost state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('hungarian');
  await page.locator('.algo-card[data-key="dp/hungarian"]').click();
  await page.locator('.example-select').selectOption({ label: 'Worker assignment' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-costs')).toHaveValue('9,2,7;6,4,3;5,8,1');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('min cost');
  await expect(page.locator('#state-content')).toContainText('assignment');
  await expect(page.locator('#state-content')).toContainText('reduced matrix');
});

test('runs suffix array and shows suffix search state', async ({ page }) => {
  await page.goto('/');

  await page.locator('#algorithm-search').fill('suffix_array');
  await page.locator('.algo-card[data-key="string/suffix_array"]').click();
  await page.locator('.example-select').selectOption({ label: 'Banana search' });
  await page.getByRole('button', { name: 'Load' }).click();

  await expect(page.locator('#param-text')).toHaveValue('banana');
  await expect(page.locator('#param-pattern')).toHaveValue('ana');

  await page.locator('#speed-slider').fill('50');
  await page.locator('#btn-play').click();

  await expect(page.locator('#status-badge')).toHaveText('Finished', { timeout: 15_000 });
  await expect(page.locator('#state-panel')).toBeVisible();
  await expect(page.locator('#state-content')).toContainText('suffix array');
  await expect(page.locator('#state-content')).toContainText('matches');
  await expect(page.locator('#state-content')).toContainText('ranks');
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
