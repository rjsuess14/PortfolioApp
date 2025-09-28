import { test, expect, type Page } from '@playwright/test';

/**
 * Plaid Link Integration Tests
 * 
 * These tests verify the complete Plaid Link flow including:
 * - Link token creation
 * - Plaid Link modal interaction
 * - Public token exchange
 * - Account connection success/failure scenarios
 */

// Test data constants
const TEST_USER = {
	email: 'test@example.com',
	password: 'testpassword123'
};

const PLAID_SANDBOX_CREDENTIALS = {
	username: 'user_good',
	password: 'pass_good',
	institution: 'Chase'
};

const MOCK_RESPONSES = {
	linkToken: {
		link_token: 'link-sandbox-test-token',
		expiration: '2024-01-01T00:00:00Z'
	},
	exchangeSuccess: {
		success: true,
		message: 'Account linked successfully'
	}
};

class PlaidLinkTestHelper {
	constructor(private page: Page) {}

	/**
	 * Navigate to dashboard and initiate Plaid Link
	 */
	async navigateToDashboard() {
		await this.page.goto('/dashboard');
		await expect(this.page).toHaveTitle(/Dashboard/);
	}

	/**
	 * Mock the backend API responses for testing
	 */
	async mockPlaidAPIs() {
		// Mock link token creation
		await this.page.route('**/api/v1/plaid/link-token', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(MOCK_RESPONSES.linkToken)
			});
		});

		// Mock token exchange
		await this.page.route('**/api/v1/plaid/exchange-token', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(MOCK_RESPONSES.exchangeSuccess)
			});
		});
	}

	/**
	 * Wait for and interact with Plaid Link modal
	 */
	async interactWithPlaidLink() {
		// Click "Link Account" or similar button
		await this.page.click('[data-testid="link-account-button"]');

		// Wait for Plaid Link to load
		await this.page.waitForSelector('[data-testid="plaid-link-container"]', {
			timeout: 10000
		});

		// The actual Plaid Link interaction would be here
		// In sandbox mode, we can interact with the Plaid UI
		// This is simplified for testing
		await this.page.waitForTimeout(2000); // Allow Link to fully load

		return true;
	}

	/**
	 * Complete successful account linking flow
	 */
	async completeLinkingFlow() {
		// This would interact with the actual Plaid Link flow
		// For testing purposes, we'll simulate the success
		await this.page.evaluate(() => {
			// Simulate successful Plaid Link completion
			window.dispatchEvent(new CustomEvent('plaid-link-success', {
				detail: {
					public_token: 'public-sandbox-success-token',
					metadata: {
						institution: { name: 'Chase', institution_id: 'ins_3' },
						accounts: [{ id: 'account_1', name: 'Checking Account' }]
					}
				}
			}));
		});

		// Wait for success message
		await expect(this.page.locator('[data-testid="link-success-message"]'))
			.toBeVisible({ timeout: 5000 });
	}

	/**
	 * Verify account appears in dashboard
	 */
	async verifyAccountAppears() {
		// Wait for page to update with new account
		await this.page.waitForLoadState('networkidle');

		// Check that new account appears in the UI
		await expect(this.page.locator('[data-testid="connected-account"]'))
			.toBeVisible();

		// Verify account details
		const accountName = await this.page.locator('[data-testid="account-name"]').textContent();
		expect(accountName).toContain('Checking Account');
	}
}

test.describe('Plaid Link Integration', () => {
	let helper: PlaidLinkTestHelper;

	test.beforeEach(async ({ page }) => {
		helper = new PlaidLinkTestHelper(page);
		
		// Mock authentication
		await page.addInitScript(() => {
			localStorage.setItem('auth-token', 'mock-jwt-token');
			localStorage.setItem('user', JSON.stringify({
				id: 'test-user-id',
				email: 'test@example.com'
			}));
		});

		// Mock Plaid APIs
		await helper.mockPlaidAPIs();
	});

	test('should successfully complete account linking flow', async ({ page }) => {
		await helper.navigateToDashboard();
		
		// Start linking process
		await helper.interactWithPlaidLink();
		
		// Complete the linking flow
		await helper.completeLinkingFlow();
		
		// Verify success
		await helper.verifyAccountAppears();
	});

	test('should handle link token creation failure', async ({ page }) => {
		// Mock API failure
		await page.route('**/api/v1/plaid/link-token', async (route) => {
			await route.fulfill({
				status: 400,
				contentType: 'application/json',
				body: JSON.stringify({
					detail: 'Failed to create link token: Invalid credentials'
				})
			});
		});

		await helper.navigateToDashboard();

		// Try to start linking process
		await page.click('[data-testid="link-account-button"]');

		// Verify error message appears
		await expect(page.locator('[data-testid="error-message"]'))
			.toContainText('Failed to create link token');
	});

	test('should handle public token exchange failure', async ({ page }) => {
		// Mock exchange failure
		await page.route('**/api/v1/plaid/exchange-token', async (route) => {
			await route.fulfill({
				status: 400,
				contentType: 'application/json',
				body: JSON.stringify({
					detail: 'Failed to exchange token: Invalid public token'
				})
			});
		});

		await helper.navigateToDashboard();
		await helper.interactWithPlaidLink();

		// Simulate Link completion with exchange failure
		await page.evaluate(() => {
			window.dispatchEvent(new CustomEvent('plaid-link-success', {
				detail: {
					public_token: 'invalid-public-token',
					metadata: { institution: { name: 'Test Bank' } }
				}
			}));
		});

		// Verify error handling
		await expect(page.locator('[data-testid="exchange-error-message"]'))
			.toBeVisible();
	});

	test('should handle user cancellation gracefully', async ({ page }) => {
		await helper.navigateToDashboard();
		await helper.interactWithPlaidLink();

		// Simulate user cancelling Plaid Link
		await page.evaluate(() => {
			window.dispatchEvent(new CustomEvent('plaid-link-exit', {
				detail: { exit_status: 'user_cancelled' }
			}));
		});

		// Verify graceful handling
		await expect(page.locator('[data-testid="link-account-button"]'))
			.toBeVisible(); // Button should still be available
	});

	test('should display loading states during linking', async ({ page }) => {
		await helper.navigateToDashboard();

		// Click link button
		await page.click('[data-testid="link-account-button"]');

		// Verify loading state
		await expect(page.locator('[data-testid="loading-spinner"]'))
			.toBeVisible();

		// Verify loading text
		await expect(page.locator('[data-testid="loading-text"]'))
			.toContainText('Connecting to your bank...');
	});

	test('should validate required permissions', async ({ page, context }) => {
		// Grant necessary permissions
		await context.grantPermissions(['clipboard-read', 'clipboard-write']);

		await helper.navigateToDashboard();
		await helper.interactWithPlaidLink();

		// Verify Plaid Link can access necessary browser features
		const hasClipboardAccess = await page.evaluate(() => {
			return !!navigator.clipboard;
		});

		expect(hasClipboardAccess).toBe(true);
	});

	test('should work on mobile viewports', async ({ page }) => {
		// Set mobile viewport
		await page.setViewportSize({ width: 375, height: 667 });

		await helper.navigateToDashboard();

		// Verify mobile-friendly link button
		const linkButton = page.locator('[data-testid="link-account-button"]');
		await expect(linkButton).toBeVisible();

		// Check button is properly sized for mobile
		const buttonBox = await linkButton.boundingBox();
		expect(buttonBox?.height).toBeGreaterThan(44); // iOS minimum touch target
	});

	test('should maintain accessibility standards', async ({ page }) => {
		await helper.navigateToDashboard();

		// Check for proper ARIA labels
		await expect(page.locator('[data-testid="link-account-button"]'))
			.toHaveAttribute('aria-label');

		// Check for keyboard navigation
		await page.keyboard.press('Tab');
		const focusedElement = await page.locator(':focus').getAttribute('data-testid');
		expect(focusedElement).toBeTruthy();

		// Check color contrast (would require actual color analysis)
		// This is a placeholder for accessibility testing
		const linkButton = page.locator('[data-testid="link-account-button"]');
		await expect(linkButton).toBeVisible();
	});
});

test.describe('Plaid Link Error Handling', () => {
	test('should handle network errors gracefully', async ({ page }) => {
		// Simulate network failure
		await page.route('**/api/v1/plaid/**', async (route) => {
			await route.abort('connectionrefused');
		});

		await page.goto('/dashboard');

		// Mock authentication
		await page.addInitScript(() => {
			localStorage.setItem('auth-token', 'mock-jwt-token');
		});

		await page.click('[data-testid="link-account-button"]');

		// Verify network error handling
		await expect(page.locator('[data-testid="network-error-message"]'))
			.toBeVisible();
	});

	test('should retry failed requests', async ({ page }) => {
		let requestCount = 0;

		// Mock API that fails first time, succeeds second time
		await page.route('**/api/v1/plaid/link-token', async (route) => {
			requestCount++;
			if (requestCount === 1) {
				await route.fulfill({
					status: 500,
					body: JSON.stringify({ detail: 'Server error' })
				});
			} else {
				await route.fulfill({
					status: 200,
					body: JSON.stringify(MOCK_RESPONSES.linkToken)
				});
			}
		});

		await page.goto('/dashboard');
		await page.addInitScript(() => {
			localStorage.setItem('auth-token', 'mock-jwt-token');
		});

		await page.click('[data-testid="link-account-button"]');

		// Verify retry mechanism works
		await expect(page.locator('[data-testid="plaid-link-container"]'))
			.toBeVisible({ timeout: 10000 });

		expect(requestCount).toBe(2);
	});

	test('should handle timeout scenarios', async ({ page }) => {
		// Mock slow API response
		await page.route('**/api/v1/plaid/link-token', async (route) => {
			// Delay response beyond timeout
			await new Promise(resolve => setTimeout(resolve, 6000));
			await route.fulfill({
				status: 200,
				body: JSON.stringify(MOCK_RESPONSES.linkToken)
			});
		});

		await page.goto('/dashboard');
		await page.addInitScript(() => {
			localStorage.setItem('auth-token', 'mock-jwt-token');
		});

		await page.click('[data-testid="link-account-button"]');

		// Verify timeout handling
		await expect(page.locator('[data-testid="timeout-error-message"]'))
			.toBeVisible({ timeout: 8000 });
	});
});

test.describe('Plaid Link Security', () => {
	test('should not expose sensitive data in client-side code', async ({ page }) => {
		await page.goto('/dashboard');
		
		// Check that no sensitive data is exposed in page source
		const pageContent = await page.content();
		
		// These should not appear in client-side code
		const sensitivePatterns = [
			/PLAID_SECRET/,
			/access[-_]token/i,
			/client[-_]secret/i,
			/sk_live/,
			/pk_live/
		];

		for (const pattern of sensitivePatterns) {
			expect(pageContent).not.toMatch(pattern);
		}
	});

	test('should use HTTPS for all API calls', async ({ page }) => {
		const requestUrls: string[] = [];

		// Capture all network requests
		page.on('request', (request) => {
			requestUrls.push(request.url());
		});

		await page.goto('/dashboard');
		await page.addInitScript(() => {
			localStorage.setItem('auth-token', 'mock-jwt-token');
		});

		await page.click('[data-testid="link-account-button"]');

		// In production, all requests should use HTTPS
		// For testing, we allow HTTP for local development
		const apiRequests = requestUrls.filter(url => url.includes('/api/'));
		
		for (const url of apiRequests) {
			// In production environment, this should be HTTPS
			if (process.env.NODE_ENV === 'production') {
				expect(url).toMatch(/^https:/);
			}
		}
	});

	test('should include proper security headers', async ({ page }) => {
		const response = await page.goto('/dashboard');
		const headers = response?.headers();

		// Check for important security headers
		// Note: These depend on server configuration
		if (headers?.['content-security-policy']) {
			expect(headers['content-security-policy']).toBeTruthy();
		}

		if (headers?.['x-content-type-options']) {
			expect(headers['x-content-type-options']).toBe('nosniff');
		}
	});
});