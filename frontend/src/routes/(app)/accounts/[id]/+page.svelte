<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import HoldingsTable from '$lib/components/portfolio/HoldingsTable.svelte';
  import {
    portfolioState,
    accounts,
    holdings,
    isLoading,
    error,
    portfolioActions,
    portfolioUtils
  } from '$lib/stores/portfolioStore';
  import { portfolioService } from '$lib/services/portfolioService';

  // Params
  const p = $derived($page);
  const accountId = $derived(p.params.id);

  // Local UI state
  let localLoading = $state(true);
  let localError: string | null = $state(null);
  let refreshing = $state(false);

  // Derived data from stores
  const account = $derived(portfolioUtils.getAccountById($accounts, accountId));
  const accountHoldings = $derived(portfolioUtils.getHoldingsByAccount($holdings, accountId));

  onMount(async () => {
    try {
      if (!$portfolioState.data) {
        await portfolioActions.loadPortfolio();
      }
      if (!account) {
        // If account still not found after load, surface an error
        localError = 'Account not found or not accessible.';
      }
    } catch (e) {
      localError = e instanceof Error ? e.message : 'Failed to load account';
    } finally {
      localLoading = false;
    }
  });

  async function handleRefreshAccount() {
    try {
      refreshing = true;
      await portfolioService.refreshAccount(accountId);
      await portfolioActions.loadPortfolio();
      localError = null;
    } catch (e) {
      localError = e instanceof Error ? e.message : 'Failed to refresh account';
    } finally {
      refreshing = false;
    }
  }

  function getAccountTypeDisplay(type: string): string {
    switch (type?.toLowerCase()) {
      case 'brokerage':
        return 'Brokerage';
      case 'ira':
        return 'IRA';
      case '401k':
        return '401(k)';
      case 'roth':
        return 'Roth IRA';
      case 'investment':
        return 'Investment';
      default:
        return type ? type.charAt(0).toUpperCase() + type.slice(1) : 'Account';
    }
  }

  function getAccountTypeIcon(type: string): string {
    switch (type?.toLowerCase()) {
      case 'brokerage':
        return '💼';
      case 'ira':
      case 'roth':
        return '🏛️';
      case '401k':
        return '🏢';
      default:
        return '💳';
    }
  }
</script>

{#if localLoading || $isLoading}
  <div class="min-h-[40vh] flex items-center justify-center">
    <div class="text-center">
      <svg class="animate-spin mx-auto h-10 w-10 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="mt-3 text-gray-600">Loading account…</p>
    </div>
  </div>
{:else}
  <div class="space-y-6">
    <!-- Header / Breadcrumbs -->
    <div class="flex items-center justify-between">
      <div>
        <nav class="text-sm text-gray-500 mb-1" aria-label="Breadcrumb">
          <ol class="inline-flex items-center space-x-1">
            <li>
              <a href="/dashboard" class="hover:text-gray-700">Dashboard</a>
            </li>
            <li>
              <span class="px-1">/</span>
              <span class="text-gray-700">Accounts</span>
            </li>
            {#if account}
              <li>
                <span class="px-1">/</span>
                <span class="text-gray-900">{account.account_name}</span>
              </li>
            {/if}
          </ol>
        </nav>
        <h1 class="text-2xl font-bold text-gray-900">{account ? account.account_name : 'Account'}</h1>
        {#if account}
          <p class="text-gray-600">{getAccountTypeIcon(account.account_type)} {getAccountTypeDisplay(account.account_type)}{account.institution_name ? ` • ${account.institution_name}` : ''}</p>
        {/if}
      </div>
      <div class="flex items-center space-x-3">
        <button
          class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          on:click={() => goto('/dashboard')}
        >
          ← Back
        </button>
        <button
          class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          disabled={refreshing}
          on:click={handleRefreshAccount}
        >
          <svg class="mr-2 h-4 w-4 {refreshing ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Account
        </button>
      </div>
    </div>

    {#if localError || $error}
      <div class="rounded-md bg-red-50 p-4">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Unable to load account</h3>
            <div class="mt-2 text-sm text-red-700">
              <p>{localError || $error}</p>
            </div>
          </div>
        </div>
      </div>
    {/if}

    {#if account}
      <!-- Account summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <dt class="text-sm font-medium text-gray-500">Total Account Value</dt>
            <dd class="mt-1 text-2xl font-bold text-gray-900">{portfolioUtils.formatCurrency(account.total_value)}</dd>
          </div>
        </div>
        {#if account.gain_loss !== undefined}
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <dt class="text-sm font-medium text-gray-500">Total Gain/Loss</dt>
              <dd class="mt-1 text-xl font-semibold {account.gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}">
                {portfolioUtils.formatCurrency(account.gain_loss)}
                {#if account.gain_loss_percent !== undefined}
                  <span class="ml-2 text-sm text-gray-600">({portfolioUtils.formatPercent(account.gain_loss_percent)})</span>
                {/if}
              </dd>
            </div>
          </div>
        {/if}
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <dt class="text-sm font-medium text-gray-500">Positions</dt>
            <dd class="mt-1 text-2xl font-bold text-gray-900">{accountHoldings.length}</dd>
          </div>
        </div>
      </div>

      <!-- Holdings for this account -->
      <HoldingsTable holdings={accountHoldings} showAccountColumn={false} />
    {/if}
  </div>
{/if}

<style>
  /* no-op */
</style>
