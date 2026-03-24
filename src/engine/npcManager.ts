import type { NPCConfig } from '../data/agents';
import type { NPC, Locomotion, Activity } from './npc';

export interface NPCGlobalState {
  agentId: string;
  name: string;
  currentMap: string;
  homeMap: string;
  homeTileX: number;
  homeTileY: number;
  tileX: number;
  tileY: number;
  activity: Activity;
  locomotion: Locomotion;
  /** Target map/tile for pending summon (cross-map) */
  summonTarget?: { map: string; tileX: number; tileY: number };
}

class NPCManagerClass {
  private states = new Map<string, NPCGlobalState>();

  init(registry: NPCConfig[]): void {
    this.states.clear();
    for (const reg of registry) {
      this.states.set(reg.agentId, {
        agentId: reg.agentId,
        name: reg.name,
        currentMap: reg.map,
        homeMap: reg.map,
        homeTileX: reg.tileX,
        homeTileY: reg.tileY,
        tileX: reg.tileX,
        tileY: reg.tileY,
        activity: 'idle',
        locomotion: 'stationary',
      });
    }
  }

  getStates(): NPCGlobalState[] {
    return Array.from(this.states.values());
  }

  getState(agentId: string): NPCGlobalState | undefined {
    return this.states.get(agentId);
  }

  /** Get NPCs that should be on a given map (includes summoned NPCs) */
  getNPCsForMap(mapName: string): NPCGlobalState[] {
    return this.getStates().filter((s) => s.currentMap === mapName);
  }

  /** Summon an NPC to a target map + tile */
  summon(agentId: string, targetMap: string, targetTileX: number, targetTileY: number): boolean {
    const state = this.states.get(agentId);
    if (!state) return false;
    if (state.activity === 'busy') return false; // Can't summon while busy

    state.currentMap = targetMap;
    state.locomotion = 'summoned';
    state.summonTarget = { map: targetMap, tileX: targetTileX, tileY: targetTileY };
    return true;
  }

  /** Return an NPC to its home map */
  returnHome(agentId: string): boolean {
    const state = this.states.get(agentId);
    if (!state) return false;
    if (state.activity === 'busy') return false;

    state.currentMap = state.homeMap;
    state.locomotion = 'returning';
    state.tileX = state.homeTileX;
    state.tileY = state.homeTileY;
    state.summonTarget = undefined;
    return true;
  }

  /** Sync global state from a live NPC instance */
  syncFromNPC(npc: NPC): void {
    const state = this.states.get(npc.agentId);
    if (!state) return;
    state.tileX = npc.tileCol;
    state.tileY = npc.tileRow;
    state.activity = npc.activity;
    state.locomotion = npc.locomotion;
    state.currentMap = npc.currentMap;
  }
}

export const npcManager = new NPCManagerClass();
