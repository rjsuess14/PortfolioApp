<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { onMount } from 'svelte';

	let { children } = $props();
	
	const authState = $derived($auth);

	// Redirect to login if not authenticated
	$effect(() => {
		if (!authState.loading && !authState.user) {
			window.location.href = '/login';
		}
	});

	// Handle logout
	async function handleLogout() {
		await auth.logout();
	}
</script>

{#if authState.loading}
	<div class="min-h-screen bg-gray-100 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin text-4xl mb-4">⏳</div>
			<p class="text-gray-600">Loading...</p>
		</div>
	</div>
{:else if authState.user}
	<div class="min-h-screen bg-gray-100">
		<nav class="bg-white shadow-sm border-b">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex justify-between h-16">
					<div class="flex items-center">
						<h1 class="text-xl font-semibold text-gray-900">Portfolio App</h1>
					</div>
					<div class="flex items-center space-x-4">
						<a href="/dashboard" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
							Dashboard
						</a>
						<span class="text-gray-500 text-sm">{authState.user.email}</span>
						<button 
							onclick={handleLogout}
							class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
						>
							Logout
						</button>
					</div>
				</div>
			</div>
		</nav>
		
		<main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
			{@render children?.()}
		</main>
	</div>
{:else}
	<!-- This shouldn't render due to redirect, but just in case -->
	<div class="min-h-screen bg-gray-100 flex items-center justify-center">
		<div class="text-center">
			<p class="text-gray-600">Redirecting to login...</p>
		</div>
	</div>
{/if}