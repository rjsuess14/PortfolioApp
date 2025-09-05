<script lang="ts">
	// TODO: Load portfolio data from API
	let totalPortfolioValue = 0;
	let accounts = [];
	let holdings = [];
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
		<p class="text-gray-600">Overview of your portfolio performance</p>
	</div>

	<!-- Portfolio Summary -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
								${totalPortfolioValue.toLocaleString()}
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
							<dd class="text-lg font-medium text-gray-900">{accounts.length}</dd>
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
							<dd class="text-lg font-medium text-gray-900">{holdings.length}</dd>
						</dl>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Accounts Section -->
	<div class="bg-white shadow overflow-hidden sm:rounded-md">
		<div class="px-4 py-5 sm:px-6">
			<h3 class="text-lg leading-6 font-medium text-gray-900">Your Accounts</h3>
			<p class="mt-1 max-w-2xl text-sm text-gray-500">Connected brokerage and investment accounts</p>
		</div>
		<div class="border-t border-gray-200">
			{#if accounts.length === 0}
				<div class="p-6 text-center">
					<p class="text-gray-500">No accounts connected yet.</p>
					<button class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
						Connect Account
					</button>
				</div>
			{:else}
				<!-- TODO: Render account list -->
				<p class="p-4 text-gray-500">Account list will be displayed here.</p>
			{/if}
		</div>
	</div>

	<!-- Holdings Section -->
	<div class="bg-white shadow overflow-hidden sm:rounded-md">
		<div class="px-4 py-5 sm:px-6">
			<h3 class="text-lg leading-6 font-medium text-gray-900">Current Holdings</h3>
			<p class="mt-1 max-w-2xl text-sm text-gray-500">Your current stock and investment positions</p>
		</div>
		<div class="border-t border-gray-200">
			{#if holdings.length === 0}
				<div class="p-6 text-center">
					<p class="text-gray-500">No holdings found. Connect an account to see your positions.</p>
				</div>
			{:else}
				<!-- TODO: Render holdings table -->
				<p class="p-4 text-gray-500">Holdings table will be displayed here.</p>
			{/if}
		</div>
	</div>
</div>