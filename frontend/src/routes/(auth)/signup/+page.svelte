<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let isSubmitting = $state(false);
	let showPassword = $state(false);
	let showConfirmPassword = $state(false);
	let showEmailForm = $state(false);
	let validationErrors = $state<{ email?: string; password?: string; confirmPassword?: string }>({});
	let successMessage = $state('');

	const authState = $derived($auth);

	// Initialize auth and redirect if already authenticated
	onMount(() => {
		auth.initialize();
		if (authState.user) {
			goto('/dashboard');
		}
	});

	function validateForm() {
		validationErrors = {};
		email = email.trim();

		if (!email) {
			validationErrors.email = 'Email is required';
		} else if (!/\S+@\S+\.\S+/.test(email)) {
			validationErrors.email = 'Email is invalid';
		}

		if (!password) {
			validationErrors.password = 'Password is required';
		} else if (password.length < 6) {
			validationErrors.password = 'Password must be at least 6 characters';
		}

		if (!confirmPassword) {
			validationErrors.confirmPassword = 'Please confirm your password';
		} else if (password !== confirmPassword) {
			validationErrors.confirmPassword = 'Passwords do not match';
		}

		return Object.keys(validationErrors).length === 0;
	}

	async function handleSignup() {
		if (!validateForm()) return;

		isSubmitting = true;
		auth.clearError();
		successMessage = '';

		const result = await auth.register(email, password);

		if (result.success) {
			if (result.message) {
				successMessage = result.message;
			}
		}

		isSubmitting = false;
	}

	const signupWith = async (provider: 'google' | 'apple') => {
		try {
			const anyAuth: any = auth as any;
			if (typeof anyAuth.loginWithProvider === 'function') {
				await anyAuth.loginWithProvider(provider);
			} else if (typeof anyAuth.signInWithOAuth === 'function') {
				await anyAuth.signInWithOAuth(provider);
			} else {
				console.warn(`${provider} sign-up not wired yet.`);
			}
		} catch (e) {
			console.error(e);
		}
	};
</script>

<!-- Split layout -->
<div class="grid min-h-screen grid-cols-1 lg:grid-cols-2">
	<!-- Left / Hero -->
	<section class="relative flex flex-col justify-center p-8 sm:p-12 lg:p-16">
		<a href="/" class="absolute left-6 top-6 inline-flex h-12 w-12 items-center justify-center rounded-md border border-gray-200 bg-white text-sm font-semibold text-gray-700">Logo</a>
		<div class="max-w-2xl">
			<h1 class="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">Personal Portfolio Manager</h1>
			<p class="mt-4 text-lg text-gray-600">Manage your investments like a professional</p>
		</div>
	</section>

	<!-- Right / Auth options -->
	<aside class="flex items-center justify-center bg-gray-100 px-6 py-12 sm:px-8 lg:px-12">
		<div class="w-full max-w-md">
			<h2 class="text-center text-2xl font-semibold text-gray-900">Create an Account</h2>

			<div class="mt-6 space-y-4">
				<button type="button" class="w-full rounded-full bg-black px-4 py-3 text-base font-medium text-white shadow hover:opacity-90 focus:outline-none" onclick={() => signupWith('google')}>
					Sign in with Google
				</button>
				<button type="button" class="w-full rounded-full bg-black px-4 py-3 text-base font-medium text-white shadow hover:opacity-90 focus:outline-none" onclick={() => signupWith('apple')}>
					Sign in with Apple
				</button>
				<button type="button" class="w-full rounded-full bg-black px-4 py-3 text-base font-medium text-white shadow hover:opacity-90 focus:outline-none" onclick={() => (showEmailForm = !showEmailForm)}>
					Sign in with Email
				</button>
			</div>

			<p class="mt-3 text-center text-sm text-gray-600">
				Already have an account? <a href="/login" class="font-medium underline">Login</a>
			</p>

			{#if successMessage}
				<div class="mt-6 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-700">{successMessage}</div>
			{/if}
			{#if authState.error}
				<div class="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{authState.error}</div>
			{/if}

			{#if showEmailForm}
				<form class="mt-6 space-y-5" onsubmit={(e) => { e.preventDefault(); handleSignup(); }}>
					<!-- Email Field -->
					<div class="group">
						<label for="email" class="mb-2 block text-sm font-medium text-gray-700">Email address</label>
						<div class="relative">
							<input
								id="email"
								name="email"
								type="email"
								autocomplete="email"
								required
								disabled={isSubmitting}
								bind:value={email}
								class="block w-full rounded-xl border-2 border-gray-300 px-3 py-3 text-gray-900 placeholder-gray-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:cursor-not-allowed disabled:opacity-50"
								placeholder="Enter your email"
							/>
						</div>
						{#if validationErrors.email}
							<p class="mt-2 flex items-center text-sm text-red-600">{validationErrors.email}</p>
						{/if}
					</div>

					<!-- Password Field -->
					<div class="group">
						<label for="password" class="mb-2 block text-sm font-medium text-gray-700">Password</label>
						<div class="relative">
							<input
								id="password"
								name="password"
								type={showPassword ? 'text' : 'password'}
								autocomplete="new-password"
								required
								disabled={isSubmitting}
								bind:value={password}
								class="block w-full rounded-xl border-2 border-gray-300 px-3 py-3 pr-12 text-gray-900 placeholder-gray-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:cursor-not-allowed disabled:opacity-50"
								placeholder="Create a password"
							/>
							<button type="button" class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600" onclick={() => (showPassword = !showPassword)}>
								{#if showPassword}
									<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.05 8.05M9.878 9.878a3 3 0 105.656 5.656l1.828 1.828M8.05 8.05L3 3m5.05 5.05L18 18"/></svg>
								{:else}
									<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
								{/if}
							</button>
						</div>
						{#if validationErrors.password}
							<p class="mt-2 flex items-center text-sm text-red-600">{validationErrors.password}</p>
						{/if}
					</div>

					<!-- Confirm Password Field -->
					<div class="group">
						<label for="confirm-password" class="mb-2 block text-sm font-medium text-gray-700">Confirm Password</label>
						<div class="relative">
							<input
								id="confirm-password"
								name="confirm-password"
								type={showConfirmPassword ? 'text' : 'password'}
								autocomplete="new-password"
								required
								disabled={isSubmitting}
								bind:value={confirmPassword}
								class="block w-full rounded-xl border-2 border-gray-300 px-3 py-3 pr-12 text-gray-900 placeholder-gray-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:cursor-not-allowed disabled:opacity-50"
								placeholder="Confirm your password"
							/>
							<button type="button" class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600" onclick={() => (showConfirmPassword = !showConfirmPassword)}>
								{#if showConfirmPassword}
									<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.05 8.05M9.878 9.878a3 3 0 105.656 5.656l1.828 1.828M8.05 8.05L3 3m5.05 5.05L18 18"/></svg>
								{:else}
									<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
								{/if}
							</button>
						</div>
						{#if validationErrors.confirmPassword}
							<p class="mt-2 flex items-center text-sm text-red-600">{validationErrors.confirmPassword}</p>
						{/if}
					</div>

					<button type="submit" disabled={isSubmitting} class="w-full rounded-full bg-black px-4 py-3 text-base font-medium text-white shadow hover:opacity-90 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50">
						{#if isSubmitting}Creating your account...{:else}Create your free account{/if}
					</button>
				</form>
			{/if}
		</div>
	</aside>
</div>