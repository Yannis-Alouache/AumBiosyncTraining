/** Helpers around the fatigue index (0 = rested, 100 = exhaustion).
 *  Display labels stay French: they are product content. */

export type FatigueLevel = 'ok' | 'warning' | 'critical';

export function fatigueLevel(index: number | null | undefined): FatigueLevel {
  if (index === null || index === undefined) {
    return 'ok';
  }
  if (index >= 75) {
    return 'critical';
  }
  if (index >= 40) {
    return 'warning';
  }
  return 'ok';
}

export function fatigueLabel(index: number | null | undefined): string {
  return {
    ok: 'Serein',
    warning: 'Vigilance',
    critical: 'Critique',
  }[fatigueLevel(index)];
}

export function roleLabel(role: string): string {
  return {
    SUPERVISOR: 'Superviseur QHSE',
    PLANNER: 'Planificateur',
    ADMIN: 'Administrateur',
  }[role] ?? role;
}

export function alertTypeLabel(type: string): string {
  return {
    FATIGUE_CRITICAL: 'Fatigue critique',
    INSUFFICIENT_RECOVERY: 'Récupération insuffisante',
    LOW_HRV: 'HRV basse',
    OVERTIME: 'Dépassement horaire',
    STAFFING_SHORTAGE: 'Planning sous tension',
  }[type] ?? type;
}

export function alertStatusLabel(status: string): string {
  return {
    NEW: 'Nouvelle',
    ACKNOWLEDGED: 'Acquittée',
    RESOLVED: 'Résolue',
  }[status] ?? status;
}

export function severityClass(severity: string): string {
  return { CRITICAL: 'critical', WARNING: 'warning', INFO: 'info' }[severity] ?? 'neutral';
}

export function agentStatusLabel(status: string): string {
  return {
    ACTIVE: 'Actif',
    LEAVE: 'Congé',
    TRAINING: 'Formation',
    SUSPENDED: 'Suspendu',
  }[status] ?? status;
}

export function agentStatusClass(status: string): string {
  return { ACTIVE: 'ok', LEAVE: 'neutral', TRAINING: 'info', SUSPENDED: 'critical' }[status] ?? 'neutral';
}
