/**
 * Change log (updated 2026-06-26 16:38 KST):
 * - Added a local-agent provider registry entry for OpenRouter-backed Python
 *   workflows that report Pixel Agents hook events directly.
 * - Added helper functions for selecting an active provider by id or environment
 *   variable while keeping Claude as the default provider.
 *
 * Provider registry: re-exports all bundled providers.
 *
 * Adding a new CLI provider:
 *   1. Create `server/src/providers/hook/<cli>/<cli>.ts` implementing HookProvider.
 *      (File-based and stream-based provider types will land when the first such
 *       provider ships.)
 *   2. Add an export line below.
 *
 * The adapter (VS Code extension, standalone CLI, etc.) imports from here rather
 * than reaching into each provider directory directly.
 */

import type { HookProvider } from '../../../core/src/provider.js';
import { claudeProvider } from './hook/claude/claude.js';
import { localAgentProvider } from './hook/local-agent/localAgent.js';

export { claudeProvider } from './hook/claude/claude.js';
export { copyHookScript } from './hook/claude/claudeHookInstaller.js';
export { localAgentProvider } from './hook/local-agent/localAgent.js';

export const bundledProviders = [claudeProvider, localAgentProvider] as const;

export function getProviderById(providerId: string | undefined): HookProvider {
  if (!providerId) return claudeProvider;
  return bundledProviders.find((provider) => provider.id === providerId) ?? claudeProvider;
}

export function getProviderFromEnv(): HookProvider {
  return getProviderById(process.env['PIXEL_AGENTS_PROVIDER']);
}
