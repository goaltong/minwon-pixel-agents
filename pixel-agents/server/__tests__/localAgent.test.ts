/**
 * Change log (created 2026-06-26 16:38 KST):
 * - Updated 2026-06-30 12:17 KST:
 *   * Saved a backup before editing at OLD/localAgent.test_Ver.2606301217.ts.
 *   * Updated lifecycle expectations so completed local-agent workflows emit a
 *     sessionEnd event and are removed from the Pixel Agents room after each
 *     Python/OpenRouter run.
 * - Updated 2026-06-30 00:00 KST:
 *   * Saved a backup before editing at OLD/localAgent.test_Ver.2606300000.ts.
 *   * Updated lifecycle expectations so completed one-shot local-agent workflows
 *     keep their character visible instead of removing the session.
 * - Added tests for the local-agent provider used by OpenRouter-backed Python
 *   workflows that emit Pixel Agents hook events directly.
 */

import { describe, expect, it } from 'vitest';

import { localAgentProvider } from '../src/providers/hook/local-agent/localAgent.js';

describe('localAgentProvider', () => {
  it('normalizes session lifecycle events', () => {
    expect(
      localAgentProvider.normalizeHookEvent({
        hook_event_name: 'SessionStart',
        session_id: 'sess-1',
        cwd: 'D:\\AI_Champion\\Agent',
      }),
    ).toEqual({
      sessionId: 'sess-1',
      event: {
        kind: 'sessionStart',
        source: 'local-agent',
        cwd: 'D:\\AI_Champion\\Agent',
      },
    });

    expect(
      localAgentProvider.normalizeHookEvent({
        hook_event_name: 'SessionEnd',
        session_id: 'sess-1',
        reason: 'completed',
      }),
    ).toEqual({
      sessionId: 'sess-1',
      event: { kind: 'sessionEnd', reason: 'completed' },
    });

    expect(
      localAgentProvider.normalizeHookEvent({
        hook_event_name: 'SessionEnd',
        session_id: 'sess-1',
        reason: 'exit',
      }),
    ).toEqual({
      sessionId: 'sess-1',
      event: { kind: 'sessionEnd', reason: 'exit' },
    });
  });

  it('normalizes explicit stage tool ids', () => {
    expect(
      localAgentProvider.normalizeHookEvent({
        hook_event_name: 'PreToolUse',
        session_id: 'sess-1',
        tool_id: 'ClassificationAgent-1',
        tool_name: 'ClassificationAgent',
        tool_input: { complaint_id: 'C-1' },
      }),
    ).toEqual({
      sessionId: 'sess-1',
      event: {
        kind: 'toolStart',
        toolId: 'ClassificationAgent-1',
        toolName: 'ClassificationAgent',
        input: { complaint_id: 'C-1' },
      },
    });

    expect(
      localAgentProvider.normalizeHookEvent({
        hook_event_name: 'PostToolUse',
        session_id: 'sess-1',
        tool_id: 'ClassificationAgent-1',
      }),
    ).toEqual({
      sessionId: 'sess-1',
      event: { kind: 'toolEnd', toolId: 'ClassificationAgent-1' },
    });
  });

  it('formats complaint workflow statuses', () => {
    expect(
      localAgentProvider.formatToolStatus('DraftAgent', { complaint_id: 'C-1' }),
    ).toBe('Drafting response (C-1)');
    expect(localAgentProvider.formatToolStatus('OpenRouter', { model: 'microsoft/phi-4' })).toBe(
      'Calling OpenRouter: phi-4',
    );
  });
});
