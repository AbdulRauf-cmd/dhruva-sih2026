import Dexie from 'dexie';

class DhruvaDB extends Dexie {
  events!: Dexie.Table<any, string>;
  pendingActions!: Dexie.Table<any, number>;
  cachedData!: Dexie.Table<any, string>;

  constructor() {
    super('dhruva');
    this.version(1).stores({
      events: 'id, type, node_id, lamport_clock, synced',
      pendingActions: '++id, type, created_at',
      cachedData: 'key',
    });
  }
}

export const db = new DhruvaDB();
