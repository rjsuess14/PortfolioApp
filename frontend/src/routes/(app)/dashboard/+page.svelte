<script lang="ts">
	import { onMount } from 'svelte';
	import PlaidLink from '$lib/components/plaid/PlaidLink.svelte';
	import AccountCard from '$lib/components/portfolio/AccountCard.svelte';
	import HoldingsTable from '$lib/components/portfolio/HoldingsTable.svelte';
	import { 
		portfolioState,
		accounts,
		holdings,
		totalValue,
		isLoading,
		error,
		linkingState,
		portfolioActions,
		linkingActions,
		portfolioUtils
	} from '$lib/stores/portfolioStore';
	
	let showNotificationFlag = false;
	let notificationMessage = '';
	let notificationType: 'success' | 'error' = 'success';
	
	// Load portfolio data on component mount
	onMount(() => {
		portfolioActions.loadPortfolio();
		
		// Listen for stock navigation events
		const handleViewStock = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { symbol } = customEvent.detail;
			// Navigate to stock detail page
			window.location.href = `/stock/${symbol}`;
		};
		
		const handleViewDetails = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { accountId } = customEvent.detail;
			// Navigate to the new account detail page
			window.location.href = `/accounts/${accountId}`;
		};
		
		const handleRefreshAccount = (event: Event) => {
			const customEvent = event as CustomEvent;
			const { accountId } = customEvent.detail;
			// Refresh specific account
			console.log('Refresh account:', accountId);
			// TODO: Implement account refresh
		};
		
		// Add event listeners
		document.addEventListener('viewStock', handleViewStock);
		document.addEventListener('viewDetails', handleViewDetails);
		document.addEventListener('refreshAccount', handleRefreshAccount);
		
		// Cleanup
		return () => {
			document.removeEventListener('viewStock', handleViewStock);
			document.removeEventListener('viewDetails', handleViewDetails);
			document.removeEventListener('refreshAccount', handleRefreshAccount);
		};
	});
	
    // Handle PlaidLink success
    function handleLinkSuccess(event: CustomEvent) {
        // PlaidLink component already exchanges the token; we only need to refresh
        const { metadata } = event.detail;
        linkingActions.handleLinkSuccess(undefined, metadata);
        showNotification('Account linked successfully!', 'success');
    }
	
	// Handle PlaidLink error
	function handleLinkError(event: CustomEvent) {
		const { error } = event.detail;
		linkingActions.handleLinkError(error);
		showNotification('Failed to link account. Please try again.', 'error');
	}
	
	// Handle PlaidLink exit
	function handleLinkExit(event: CustomEvent) {
		linkingActions.handleLinkExit();
	}
	
	// Show notification
	function showNotification(message: string, type: 'success' | 'error' = 'success') {
		notificationMessage = message;
		notificationType = type;
		showNotificationFlag = true;
		
		// Auto-hide after 5 seconds
		setTimeout(() => {
			showNotificationFlag = false;
		}, 5000);
	}
	
	// Handle refresh
	async function handleRefresh() {
		try {
			await portfolioActions.refreshPortfolio();
			showNotification('Portfolio refreshed successfully!', 'success');
		} catch (err) {
			showNotification('Failed to refresh portfolio. Please try again.', 'error');
		}
	}
	
	// Calculate total gain/loss
	$: totalGainLoss = portfolioUtils.getTotalGainLoss($holdings);
</script>

<!-- Notification -->
{#if showNotificationFlag}
	<div class="fixed top-4 right-4 z-50 max-w-sm">
		<div class="rounded-md p-4 {notificationType === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}">
			<div class="flex">
				<div class="flex-shrink-0">
					{#if notificationType === 'success'}
						<svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
						</svg>
					{:else}
						<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
						</svg>
					{/if}
				</div>
				<div class="ml-3">
					<p class="text-sm font-medium">{notificationMessage}</p>
				</div>
				<div class="ml-auto pl-3">
					<button 
						class="inline-flex rounded-md p-1.5 hover:bg-gray-100"
						on:click={() => showNotificationFlag = false}
						aria-label="Close notification"
					>
						<svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<div class="space-y-6">
	<!-- Header with Refresh -->
	<div class="flex justify-between items-center">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
			<p class="text-gray-600">Overview of your portfolio performance</p>
		</div>
		<div class="flex items-center space-x-4">
			{#if $portfolioState.lastUpdated}
				<span class="text-sm text-gray-500">
					Last updated: {$portfolioState.lastUpdated.toLocaleTimeString()}
				</span>
			{/if}
			<button
				class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				on:click={handleRefresh}
				disabled={$isLoading}
			>
				<svg class="mr-2 h-4 w-4 {$isLoading ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				Refresh
			</button>
		</div>
	</div>

	<!-- Loading State -->
	{#if $isLoading && !$portfolioState.data}
		<div class="text-center py-12">
			<svg class="animate-spin mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
			</svg>
			<p class="mt-4 text-gray-600">Loading your portfolio...</p>
		</div>
	{:else}

	<!-- Error State -->
	{#if $error}
		<div class="rounded-md bg-red-50 p-4">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
					</svg>
				</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error loading portfolio</h3>
					<div class="mt-2 text-sm text-red-700">
						<p>{$error}</p>
					</div>
					<div class="mt-4">
						<button
							type="button"
							class="bg-red-100 px-2 py-1.5 rounded-md text-sm font-medium text-red-800 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
							on:click={() => portfolioActions.clearError()}
						>
							Dismiss
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Portfolio Summary -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
							<span class="text-white text-sm font-bold">$</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Total Portfolio Value</dt>
							<dd class="text-lg font-medium text-gray-900">
								{portfolioUtils.formatCurrency($totalValue)}
							</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>
		
		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
							<span class="text-white text-sm font-bold">#</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Connected Accounts</dt>
							<dd class="text-lg font-medium text-gray-900">{$accounts.length}</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>
		
		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
							<span class="text-white text-sm font-bold">📈</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Total Holdings</dt>
							<dd class="text-lg font-medium text-gray-900">{$holdings.length}</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>

		<div class="bg-white overflow-hidden shadow rounded-lg">
			<div class="p-5">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<div class="w-8 h-8 {totalGainLoss.amount >= 0 ? 'bg-green-500' : 'bg-red-500'} rounded-full flex items-center justify-center">
							<span class="text-white text-sm font-bold">{totalGainLoss.amount >= 0 ? '↗' : '↘'}</span>
						</div>
					</div>
					<div class="ml-5 w-0 flex-1">
						<dl>
							<dt class="text-sm font-medium text-gray-500 truncate">Total Gain/Loss</dt>
							<dd class="text-lg font-medium {totalGainLoss.amount >= 0 ? 'text-green-600' : 'text-red-600'}">
								{portfolioUtils.formatCurrency(totalGainLoss.amount)}
								<div class="text-sm">
									({portfolioUtils.formatPercent(totalGainLoss.percent)})
								</div>
							</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Accounts Section -->
	<div class="bg-white shadow overflow-hidden sm:rounded-md">
		<div class="px-4 py-5 sm:px-6 flex justify-between items-center">
			<div>
				<h3 class="text-lg leading-6 font-medium text-gray-900">Your Accounts</h3>
				<p class="mt-1 max-w-2xl text-sm text-gray-500">Connected brokerage and investment accounts</p>
			</div>
			{#if $accounts.length > 0}
				<PlaidLink 
					buttonText="Add Account" 
					buttonClass="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
					on:success={handleLinkSuccess}
					on:error={handleLinkError}
					on:exit={handleLinkExit}
				/>
			{/if}
		</div>
		
		{#if $accounts.length === 0}
			<div class="border-t border-gray-200 p-6 text-center">
				<div class="text-gray-400 text-6xl mb-4">🏦</div>
				<h3 class="text-lg font-medium text-gray-900 mb-2">No accounts connected</h3>
				<p class="text-gray-500 mb-4">Connect your brokerage account to track your investments and portfolio performance.</p>
				<PlaidLink 
					buttonText="Connect Your First Account" 
					on:success={handleLinkSuccess}
					on:error={handleLinkError}
					on:exit={handleLinkExit}
					disabled={$linkingState.linking}
				/>
			</div>
		{:else}
			<div class="border-t border-gray-200 p-6">
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					{#each $accounts as account (account.id)}
						<AccountCard {account} />
					{/each}
				</div>
			</div>
		{/if}
	</div>

	<!-- Holdings Section -->
	<HoldingsTable holdings={$holdings} />
	
	{/if}
</div>
