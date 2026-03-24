import { useEffect, useState } from 'react';

const MAP_DISPLAY_NAMES: Record<string, string> = {
  'world': 'ClawWorld',
  'lab-interior': 'Claw Town Lab',
  'analyst-office': 'Analyst Office',
  'coder-workshop': 'Coder Workshop',
  'guild-hall-interior': 'Guild Hall',
  'townhall-interior': 'Town Hall',
};

interface HUDProps {
  currentMap: string;
  zoneName: string | null;
}

export function HUD({ currentMap, zoneName }: HUDProps) {
  const [visible, setVisible] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [zoneVisible, setZoneVisible] = useState(false);
  const [zoneDisplay, setZoneDisplay] = useState('');

  // Map name banner (on map transition)
  useEffect(() => {
    const name = MAP_DISPLAY_NAMES[currentMap] ?? currentMap;
    setDisplayName(name);
    setVisible(true);

    const timer = setTimeout(() => setVisible(false), 2000);
    return () => clearTimeout(timer);
  }, [currentMap]);

  // Zone label (on district change within world map)
  useEffect(() => {
    if (!zoneName) {
      setZoneVisible(false);
      return;
    }
    setZoneDisplay(zoneName);
    setZoneVisible(true);

    const timer = setTimeout(() => setZoneVisible(false), 2000);
    return () => clearTimeout(timer);
  }, [zoneName]);

  return (
    <div style={{
      position: 'absolute',
      top: 24,
      left: '50%',
      transform: 'translateX(-50%)',
      pointerEvents: 'none',
      zIndex: 10,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 4,
    }}>
      <div
        style={{
          padding: '8px 24px',
          background: 'rgba(0, 0, 0, 0.7)',
          color: '#fff',
          fontFamily: '"Press Start 2P", monospace',
          fontSize: 14,
          borderRadius: 4,
          border: '2px solid rgba(255, 255, 255, 0.3)',
          opacity: visible ? 1 : 0,
          transition: 'opacity 0.4s ease',
        }}
      >
        {displayName}
      </div>
      <div
        style={{
          padding: '4px 16px',
          background: 'rgba(0, 0, 0, 0.6)',
          color: '#ccc',
          fontFamily: '"Press Start 2P", monospace',
          fontSize: 10,
          borderRadius: 3,
          border: '1px solid rgba(255, 255, 255, 0.2)',
          opacity: zoneVisible ? 1 : 0,
          transition: 'opacity 0.4s ease',
        }}
      >
        {zoneDisplay}
      </div>
    </div>
  );
}
