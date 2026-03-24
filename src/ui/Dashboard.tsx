import { useEffect, useState } from 'react';
import { useWorldStore } from '../store/world';
import { npcManager, type NPCGlobalState } from '../engine/npcManager';

const MAP_NAMES: Record<string, string> = {
  'world': 'ClawWorld',
  'lab-interior': 'Lab',
  'analyst-office': 'Analyst Office',
  'coder-workshop': 'Coder Workshop',
  'guild-hall-interior': 'Guild Hall',
  'townhall-interior': 'Town Hall',
};

function statusColor(state: NPCGlobalState): string {
  if (state.activity === 'busy') return '#f44';
  if (state.locomotion !== 'stationary') return '#fc4';
  return '#4f4';
}

function statusText(state: NPCGlobalState): string {
  if (state.activity === 'busy') return 'Busy';
  if (state.locomotion === 'summoned') return 'Summoned';
  if (state.locomotion === 'returning') return 'Returning';
  if (state.locomotion === 'wandering') return 'Walking';
  return 'Idle';
}

export function Dashboard({ onSummon, onReturn }: {
  onSummon: (agentId: string) => void;
  onReturn: (agentId: string) => void;
}) {
  const dashboardOpen = useWorldStore((s) => s.dashboardOpen);
  const currentMap = useWorldStore((s) => s.currentMap);
  const toggleDashboard = useWorldStore((s) => s.toggleDashboard);
  const [states, setStates] = useState<NPCGlobalState[]>([]);

  // Refresh NPC states every 500ms
  useEffect(() => {
    if (!dashboardOpen) return;
    const update = () => setStates(npcManager.getStates());
    update();
    const interval = setInterval(update, 500);
    return () => clearInterval(interval);
  }, [dashboardOpen]);

  if (!dashboardOpen) return null;

  return (
    <div style={{
      position: 'absolute',
      top: 8,
      right: 8,
      width: 320,
      maxHeight: 'calc(100% - 16px)',
      background: 'rgba(20, 20, 30, 0.92)',
      border: '2px solid #556',
      borderRadius: 8,
      color: '#eee',
      fontFamily: 'monospace',
      fontSize: 12,
      overflow: 'auto',
      zIndex: 100,
      pointerEvents: 'auto',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid #445',
        fontWeight: 'bold',
        fontSize: 14,
      }}>
        <span>Agent Dashboard</span>
        <button
          onClick={toggleDashboard}
          style={{
            background: 'none',
            border: '1px solid #888',
            color: '#ccc',
            cursor: 'pointer',
            borderRadius: 4,
            padding: '2px 8px',
            fontSize: 12,
          }}
        >
          ESC
        </button>
      </div>

      {/* NPC list */}
      {states.map((s) => {
        const onSameMap = s.currentMap === currentMap;
        const atHome = s.currentMap === s.homeMap;
        const canSummon = !onSameMap && s.activity !== 'busy';
        const canReturn = !atHome && s.activity !== 'busy';

        return (
          <div
            key={s.agentId}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 12px',
              borderBottom: '1px solid #333',
            }}
          >
            {/* Status dot */}
            <div style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: statusColor(s),
              flexShrink: 0,
              boxShadow: s.activity === 'busy' ? '0 0 6px #f44' : undefined,
            }} />

            {/* Name + location */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontWeight: 'bold',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {s.name}
              </div>
              <div style={{ color: '#999', fontSize: 10 }}>
                {MAP_NAMES[s.currentMap] ?? s.currentMap} — {statusText(s)}
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
              <button
                disabled={!canSummon}
                onClick={() => onSummon(s.agentId)}
                style={{
                  background: canSummon ? '#2a5' : '#333',
                  border: 'none',
                  color: canSummon ? '#fff' : '#666',
                  cursor: canSummon ? 'pointer' : 'default',
                  borderRadius: 3,
                  padding: '2px 6px',
                  fontSize: 10,
                }}
                title={canSummon ? 'Summon to your map' : onSameMap ? 'Already here' : 'NPC is busy'}
              >
                Call
              </button>
              <button
                disabled={!canReturn}
                onClick={() => onReturn(s.agentId)}
                style={{
                  background: canReturn ? '#a52' : '#333',
                  border: 'none',
                  color: canReturn ? '#fff' : '#666',
                  cursor: canReturn ? 'pointer' : 'default',
                  borderRadius: 3,
                  padding: '2px 6px',
                  fontSize: 10,
                }}
                title={canReturn ? 'Send home' : 'Already home'}
              >
                Return
              </button>
            </div>
          </div>
        );
      })}

      <div style={{ padding: '6px 12px', color: '#666', fontSize: 10, textAlign: 'center' }}>
        Press Tab to toggle
      </div>
    </div>
  );
}
