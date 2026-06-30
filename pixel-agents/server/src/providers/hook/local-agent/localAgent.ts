/**
 * Change log (created 2026-06-26 16:38 KST):
 * - Updated 2026-06-30 12:17 KST:
 *   * Saved a backup before editing at OLD/localAgent_Ver.2606301217.ts.
 *   * Changed completed local-agent SessionEnd events to emit sessionEnd again
 *     so completed Python/OpenRouter workflow characters are removed from the
 *     Pixel Agents room instead of accumulating across repeated runs.
 *   * Kept missing/null/error SessionEnd reasons ignored because they are used
 *     by best-effort reporting paths where removing the visible agent can hide
 *     useful failure context.
 * - Updated 2026-06-30 00:00 KST:
 *   * Saved a backup before editing at OLD/localAgent_Ver.2606300000.ts.
 *   * Changed completed local-agent SessionEnd events to be ignored so one-shot
 *     Python/OpenRouter workflows leave their character visible after completion.
 *   * Kept explicit exit/closed/stopped reasons mapped to sessionEnd for future
 *     long-running local agent processes.
 * - Added a hooks-only provider for local Python/OpenRouter agent workflows.
 * - Normalizes lightweight Pixel Agents hook payloads from external scripts into
 *   the common AgentEvent protocol without depending on Claude Code.
 * - Provides display labels for the complaint-practice pipeline stages used by
 *   D:\AI_Champion\Agent\multi_agent_complaint_practice.py.
 */

import * as path from 'path';

import type { AgentEvent, HookProvider } from '../../../../../core/src/provider.js';

const STAGE_LABELS: Record<string, string> = {
  ClassificationAgent: 'Classifying complaint',
  SearchAgent: 'Searching policy basis',
  DraftAgent: 'Drafting response',
  ReviewAgent: 'Reviewing draft',
};

function normalizeHookEvent(
  raw: Record<string, unknown>,
): { sessionId: string; event: AgentEvent } | null {
  const eventName = raw.hook_event_name;
  const sessionId = raw.session_id;
  if (typeof eventName !== 'string' || typeof sessionId !== 'string') return null;

  switch (eventName) {
    case 'SessionStart':
      return {
        sessionId,
        event: {
          kind: 'sessionStart',
          source: typeof raw.source === 'string' ? raw.source : 'local-agent',
          cwd: typeof raw.cwd === 'string' ? raw.cwd : undefined,
        },
      };

    case 'PreToolUse': {
      const toolName = typeof raw.tool_name === 'string' ? raw.tool_name : 'LocalAgent';
      const toolId =
        typeof raw.tool_id === 'string' && raw.tool_id ? raw.tool_id : `local-${Date.now()}`;
      const toolInput =
        typeof raw.tool_input === 'object' && raw.tool_input !== null
          ? (raw.tool_input as Record<string, unknown>)
          : {};
      return {
        sessionId,
        event: {
          kind: 'toolStart',
          toolId,
          toolName,
          input: toolInput,
        },
      };
    }

    case 'PostToolUse':
    case 'PostToolUseFailure':
      return {
        sessionId,
        event: {
          kind: 'toolEnd',
          toolId: typeof raw.tool_id === 'string' && raw.tool_id ? raw.tool_id : 'current',
        },
      };

    case 'Stop':
      return { sessionId, event: { kind: 'turnEnd', awaitingInput: true } };

    case 'SessionEnd':
      if (raw.reason === 'error' || raw.reason === undefined || raw.reason === null) {
        return null;
      }
      return {
        sessionId,
        event: {
          kind: 'sessionEnd',
          reason: typeof raw.reason === 'string' ? raw.reason : 'completed',
        },
      };

    case 'Progress':
      return {
        sessionId,
        event: {
          kind: 'progress',
          toolId: typeof raw.tool_id === 'string' && raw.tool_id ? raw.tool_id : 'current',
          data: raw.data ?? raw,
        },
      };

    default:
      return null;
  }
}

function formatToolStatus(toolName: string, input?: unknown): string {
  const inp = (input ?? {}) as Record<string, unknown>;
  const complaintId = typeof inp.complaint_id === 'string' ? inp.complaint_id : '';
  const suffix = complaintId ? ` (${complaintId})` : '';
  if (STAGE_LABELS[toolName]) return `${STAGE_LABELS[toolName]}${suffix}`;
  if (toolName === 'OpenRouter') {
    const model = typeof inp.model === 'string' ? path.basename(inp.model) : '';
    return model ? `Calling OpenRouter: ${model}` : 'Calling OpenRouter';
  }
  return `Running ${toolName}${suffix}`;
}

function installHooks(_serverUrl: string, _authToken: string): Promise<void> {
  return Promise.resolve();
}

function uninstallHooks(): Promise<void> {
  return Promise.resolve();
}

function areHooksInstalled(): Promise<boolean> {
  return Promise.resolve(true);
}

export const localAgentProvider: HookProvider = {
  kind: 'hook',
  id: 'local-agent',
  displayName: 'Local OpenRouter Agent',
  protocolVersion: 1,

  normalizeHookEvent,

  installHooks,
  uninstallHooks,
  areHooksInstalled,

  formatToolStatus,
  permissionExemptTools: new Set<string>(),
  subagentToolNames: new Set<string>(),
  readingTools: new Set(['ClassificationAgent', 'SearchAgent', 'ReviewAgent']),
  terminalNamePrefix: 'Local Agent',
};
