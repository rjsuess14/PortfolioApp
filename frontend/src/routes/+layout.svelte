<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { auth } from '$lib/stores/auth';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		auth.initialize();
		
		// Fallback timeout in case auth initialization fails silently
		setTimeout(() => {
			const currentState = $auth;
			if (currentState.loading) {
				console.warn('Auth initialization timeout, setting loading to false');
				auth.setLoaded();
			}
		}, 5000);
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children?.()}
