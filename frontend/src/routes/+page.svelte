<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	
	const authState = $derived($auth);
	
	let redirected = $state(false);
	
	// Use $effect to handle auth state changes
	$effect(() => {
		console.log('Home page auth state:', authState);
		if (!authState.loading && !redirected) {
			redirected = true;
			if (authState.user) {
				console.log('User found, redirecting to dashboard');
				goto('/dashboard');
			} else {
				console.log('No user, redirecting to login');
				goto('/login');
			}
		}
	});

	// Fallback timeout to force redirect if auth gets stuck
	$effect(() => {
		const timer = setTimeout(() => {
			if (!redirected && authState.loading) {
				console.warn('Auth taking too long, forcing redirect to login');
				auth.setLoaded();
				goto('/login');
			}
		}, 10000); // 10 second timeout

		return () => clearTimeout(timer);
	});
</script>

{#if authState.loading}
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin text-4xl mb-4">⏳</div>
			<p class="text-gray-600">Loading...</p>
		</div>
	</div>
{:else if authState.error}
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<div class="text-red-500 text-4xl mb-4">⚠️</div>
			<h1 class="text-2xl font-bold text-gray-900 mb-4">Authentication Error</h1>
			<p class="text-red-600 mb-4">{authState.error}</p>
			<button 
				onclick={() => goto('/login')}
				class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded"
			>
				Go to Login
			</button>
		</div>
	</div>
{:else}
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-gray-900 mb-4">Portfolio App</h1>
			<p class="text-gray-600">Redirecting...</p>
		</div>
	</div>
{/if}
