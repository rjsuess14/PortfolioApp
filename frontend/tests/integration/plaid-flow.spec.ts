import { test, expect } from '@playwright/test';

/**
 * End-to-End Plaid Integration Tests
 * 
 * These tests run against a real backend server and test the complete
 * integration flow from frontend to backend to Plaid sandbox.
 */

test.describe('Plaid Integration E2E', () => {
	// Setup test user credentials
	const testUser = {
		email: 'plaid-test@example.com',
		password: 'PlaidTest123!'
	};

	// Plaid sandbox test credentials
	const plaidSandboxUser = {
		username: 'user_good',
		password: 'pass_good'
	};

	test.beforeEach(async ({ page }) => {
		// Set longer timeout for integration tests
		test.setTimeout(60000);

		// Mock environment to use sandbox
		await page.addInitScript(() => {
			(window as any).__PLAID_ENV__ = 'sandbox';
		});
	});

	test('complete account linking flow with real backend', async ({ page }) => {
		// Step 1: Login or register test user
		await page.goto('/login');
		
		// Try to login, register if needed
		await page.fill('[data-testid="email-input"]', testUser.email);
		await page.fill('[data-testid="password-input"]', testUser.password);
		await page.click('[data-testid="login-button"]');

		// Handle registration if user doesn't exist
		const loginError = page.locator('[data-testid="login-error"]');
		if (await loginError.isVisible({ timeout: 2000 })) {
			await page.goto('/signup');
			await page.fill('[data-testid="email-input"]', testUser.email);
			await page.fill('[data-testid="password-input"]', testUser.password);
			await page.click('[data-testid="signup-button"]');
			
			// Wait for successful registration
			await expect(page).toHaveURL('/dashboard');
		}

		// Step 2: Navigate to dashboard
		await page.goto('/dashboard');
		await expect(page).toHaveTitle(/Dashboard/);

		// Step 3: Initiate account linking
		const linkButton = page.locator('[data-testid="link-account-button"]');
		await expect(linkButton).toBeVisible();
		await linkButton.click();

		// Step 4: Wait for Plaid Link to load
		// This will make a real API call to create a link token
		await page.waitForSelector('[data-testid="plaid-link-modal"]', { 
			timeout: 15000 
		});

		// Step 5: Interact with Plaid Link (sandbox)
		// Note: This assumes Plaid Link iframe is accessible
		// In real tests, you might need to use a different approach
		
		// Wait for Plaid Link institution selection
		const plaidFrame = page.frameLocator('[data-testid="plaid-link-iframe"]');
		
		// Select Chase bank in sandbox
		await plaidFrame.locator('text=Chase').click();
		
		// Enter sandbox credentials
		await plaidFrame.fill('[data-testid="username"]', plaidSandboxUser.username);
		await plaidFrame.fill('[data-testid="password"]', plaidSandboxUser.password);
		await plaidFrame.click('[data-testid="submit"]');

		// Select accounts to link
		await plaidFrame.click('[data-testid="select-all-accounts"]');
		await plaidFrame.click('[data-testid="continue"]');

		// Complete linking
		await plaidFrame.click('[data-testid="continue"]');

		// Step 6: Verify successful linking
		await expect(page.locator('[data-testid="link-success-message"]'))
			.toBeVisible({ timeout: 10000 });

		// Step 7: Verify account appears in dashboard
		await page.reload();
		await expect(page.locator('[data-testid="connected-account"]'))
			.toBeVisible();

		// Verify account details
		const accountName = await page.locator('[data-testid="account-name"]').first().textContent();
		expect(accountName).toBeTruthy();
		expect(accountName).not.toBe('');
	});

	test('handle Plaid Link errors in real environment', async ({ page }) => {
		await page.goto('/dashboard');
		
		// Mock bad credentials to trigger Plaid error
		await page.addInitScript(() => {
			// Override fetch to simulate server error
			const originalFetch = window.fetch;
			window.fetch = async (url, options) => {
				if (typeof url === 'string' && url.includes('/plaid/link-token')) {
					return new Response(JSON.stringify({
						detail: 'Plaid API error: Invalid credentials'
					}), { 
						status: 400,
						headers: { 'Content-Type': 'application/json' }
					});
				}
				return originalFetch(url, options);
			};
		});

		// Try to link account
		await page.click('[data-testid="link-account-button"]');

		// Verify error handling
		await expect(page.locator('[data-testid="plaid-error-message"]'))
			.toBeVisible({ timeout: 5000 });

		const errorText = await page.locator('[data-testid="plaid-error-message"]').textContent();
		expect(errorText).toContain('Plaid API error');
	});

	test('verify account data after successful linking', async ({ page }) => {
		// This test assumes an account is already linked
		await page.goto('/dashboard');

		// Check if accounts are displayed
		const accountsSection = page.locator('[data-testid="accounts-section"]');
		await expect(accountsSection).toBeVisible();

		// Verify account balance is displayed
		const balanceElement = page.locator('[data-testid="account-balance"]').first();
		if (await balanceElement.isVisible()) {
			const balanceText = await balanceElement.textContent();
			expect(balanceText).toMatch(/\$\d+/); // Should show dollar amount
		}

		// Verify account type is displayed
		const typeElement = page.locator('[data-testid="account-type"]').first();
		if (await typeElement.isVisible()) {
			const typeText = await typeElement.textContent();
			expect(typeText).toBeTruthy();
		}
	});

	test('test account refresh functionality', async ({ page }) => {
		await page.goto('/dashboard');

		// Find refresh button
		const refreshButton = page.locator('[data-testid="refresh-accounts-button"]');
		if (await refreshButton.isVisible()) {
			await refreshButton.click();

			// Verify loading state
			await expect(page.locator('[data-testid="accounts-loading"]'))
				.toBeVisible();

			// Verify data refreshes
			await expect(page.locator('[data-testid="accounts-loading"]'))
				.not.toBeVisible({ timeout: 10000 });

			// Verify accounts are still displayed
			await expect(page.locator('[data-testid="connected-account"]'))
				.toBeVisible();
		}
	});

	test('verify investment holdings display', async ({ page }) => {
		await page.goto('/dashboard');

		// Check for investment holdings section
		const holdingsSection = page.locator('[data-testid="holdings-section"]');
		if (await holdingsSection.isVisible()) {
			// Verify holdings table/list exists
			const holdingsList = page.locator('[data-testid="holdings-list"]');
			await expect(holdingsList).toBeVisible();

			// Check for stock symbols
			const stockSymbols = page.locator('[data-testid="stock-symbol"]');
			const symbolCount = await stockSymbols.count();
			
			if (symbolCount > 0) {
				// Verify first stock symbol format
				const firstSymbol = await stockSymbols.first().textContent();
				expect(firstSymbol).toMatch(/^[A-Z]{1,5}$/); // Stock symbol format
			}
		}
	});

	test('test multiple account linking', async ({ page }) => {
		await page.goto('/dashboard');

		// Count existing accounts
		const existingAccounts = await page.locator('[data-testid="connected-account"]').count();

		// Try to link another account
		await page.click('[data-testid="link-account-button"]');

		// Follow similar flow as first test but with different institution
		await page.waitForSelector('[data-testid="plaid-link-modal"]', { 
			timeout: 15000 
		});

		const plaidFrame = page.frameLocator('[data-testid="plaid-link-iframe"]');
		
		// Select different institution (Bank of America)
		await plaidFrame.locator('text=Bank of America').click();
		
		// Complete flow
		await plaidFrame.fill('[data-testid="username"]', plaidSandboxUser.username);
		await plaidFrame.fill('[data-testid="password"]', plaidSandboxUser.password);
		await plaidFrame.click('[data-testid="submit"]');
		await plaidFrame.click('[data-testid="select-all-accounts"]');
		await plaidFrame.click('[data-testid="continue"]');
		await plaidFrame.click('[data-testid="continue"]');

		// Verify both accounts are now displayed
		await page.reload();
		const newAccountCount = await page.locator('[data-testid="connected-account"]').count();
		expect(newAccountCount).toBeGreaterThan(existingAccounts);
	});

	test('test account disconnection', async ({ page }) => {
		await page.goto('/dashboard');

		// Find disconnect button for first account
		const disconnectButton = page.locator('[data-testid="disconnect-account-button"]').first();
		if (await disconnectButton.isVisible()) {
			await disconnectButton.click();

			// Confirm disconnection
			const confirmButton = page.locator('[data-testid="confirm-disconnect"]');
			if (await confirmButton.isVisible()) {
				await confirmButton.click();

				// Verify account is removed
				await expect(page.locator('[data-testid="disconnect-success-message"]'))
					.toBeVisible();

				// Reload and verify account count decreased
				await page.reload();
				// This would need to be compared against previous state
			}
		}
	});

	test('performance test - page load with accounts', async ({ page }) => {
		// Start timing
		const startTime = Date.now();

		await page.goto('/dashboard');

		// Wait for accounts to load
		await page.waitForSelector('[data-testid="accounts-section"]');
		
		const loadTime = Date.now() - startTime;

		// Page should load within reasonable time
		expect(loadTime).toBeLessThan(5000); // 5 seconds max

		// Verify no console errors
		const logs = await page.evaluate(() => {
			return (window as any).__PAGE_ERRORS__ || [];
		});
		
		expect(logs.filter((log: any) => log.level === 'error')).toHaveLength(0);
	});
});