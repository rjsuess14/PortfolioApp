import { defineConfig } from '@playwright/test';
import config from './playwright.config';

/**
 * Integration test configuration for Plaid Link testing
 * This config is specifically for testing Plaid integration flows
 */
export default defineConfig({
	...config,
	testDir: './tests/integration',
	use: {
		...config.use,
		// Use development server for integration tests
		baseURL: 'http://localhost:5173',
		// Longer timeouts for integration tests involving external services
		actionTimeout: 30000,
		navigationTimeout: 30000,
	},
	projects: [
		{
			name: 'integration-chrome',
			use: { 
				...config.projects?.[0]?.use,
				// Additional context for Plaid testing
				contextOptions: {
					permissions: ['camera', 'microphone', 'geolocation'],
					// Allow popups for Plaid Link
					viewport: { width: 1280, height: 720 }
				}
			}
		}
	],
	webServer: {
		command: 'npm run dev',
		port: 5173,
		reuseExistingServer: !process.env.CI,
		timeout: 120000 // Longer startup time for dev server
	}
});