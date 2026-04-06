export type NPCConfig = {
  agentId: string;
  name: string;
  map: string;
  tileX: number;
  tileY: number;
  facing: 'up' | 'down' | 'left' | 'right';
  portraitUrl: string;
};

export const npcRegistry: NPCConfig[] = [
  {
    agentId: 'assistant',
    name: 'Personal Assistant',
    map: 'lab-interior',
    tileX: 10,
    tileY: 7,
    facing: 'down',
    portraitUrl: '/sprites/npcs/assistant/sprite.png',
  },
  {
    agentId: 'analyst',
    name: 'Senior Analyst',
    map: 'analyst-office',
    tileX: 7,
    tileY: 5,
    facing: 'down',
    portraitUrl: '/sprites/npcs/analyst/sprite.png',
  },
  {
    agentId: 'coder',
    name: 'The Coder',
    map: 'coder-workshop',
    tileX: 7,
    tileY: 5,
    facing: 'down',
    portraitUrl: '/sprites/npcs/coder/sprite.png',
  },
  {
    agentId: 'lorekeeper',
    name: 'The Elder',
    map: 'world',
    tileX: 56,
    tileY: 18,
    facing: 'down',
    portraitUrl: '/sprites/npcs/lorekeeper/sprite.png',
  },
  {
    agentId: 'trader',
    name: 'Mysterious Trader',
    map: 'world',
    tileX: 85,
    tileY: 24,
    facing: 'down',
    portraitUrl: '/sprites/npcs/trader/sprite.png',
  },
  {
    agentId: 'jake',
    name: 'The Blacksmith',
    map: 'world',
    tileX: 15,
    tileY: 18,
    facing: 'right',
    portraitUrl: '/sprites/npcs/jake/sprite.png',
  },
  {
    agentId: 'tom',
    name: 'The Planner',
    map: 'world',
    tileX: 35,
    tileY: 18,
    facing: 'left',
    portraitUrl: '/sprites/npcs/tom/sprite.png',
  },
  {
    agentId: 'mira',
    name: 'The Innkeeper',
    map: 'world',
    tileX: 30,
    tileY: 24,
    facing: 'down',
    portraitUrl: '/sprites/npcs/mira/sprite.png',
  },
  {
    agentId: 'inspector',
    name: 'Code Inspector',
    map: 'analyst-office',
    tileX: 9,
    tileY: 5,
    facing: 'left',
    portraitUrl: '/sprites/npcs/inspector/sprite.png',
  },
  {
    agentId: 'debugger',
    name: 'Code Debugger',
    map: 'analyst-office',
    tileX: 5,
    tileY: 5,
    facing: 'right',
    portraitUrl: '/sprites/npcs/debugger/sprite.png',
  },
  {
    agentId: 'hermes-agent',
    name: 'Hermes',
    map: 'guild-hall-interior',
    tileX: 10,
    tileY: 7,
    facing: 'down',
    portraitUrl: '/sprites/npcs/hermes-agent/sprite.png',
  },
];
