/**
 * Domain models, mirroring the Quart API JSON responses.
 * Convention: fields keep the backend snake_case names.
 */

export type Role = 'SUPERVISOR' | 'PLANNER' | 'ADMIN';
export type AgentStatus = 'ACTIVE' | 'LEAVE' | 'TRAINING' | 'SUSPENDED';
export type ShiftType = 'DAY' | 'NIGHT' | 'ON_CALL';
export type ShiftStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface User {
  id: number;
  email: string;
  last_name: string;
  first_name: string;
  role: Role;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface Site {
  id: number;
  name: string;
  type: 'SDIS' | 'HOSPITAL' | 'INDUSTRY';
  city: string;
  agent_count: number;
}

export interface Agent {
  id: number;
  site_id: number;
  last_name: string;
  first_name: string;
  email: string;
  profession: string;
  grade: string;
  status: AgentStatus;
  fatigue_index: number;
  last_sleep_hours: number | null;
  hired_on: string;
  site_name: string;
  site_type: string;
  site_city: string;
}

export interface Shift {
  id: number;
  type: ShiftType;
  starts_at: string;
  ends_at: string;
  status: ShiftStatus;
  predicted_fatigue_score: number | null;
  comment: string | null;
  agent_id: number;
  site_id: number;
  agent_last_name: string;
  agent_first_name: string;
  agent_profession: string;
  site_name: string;
}

export interface Alert {
  id: number;
  type: string;
  severity: AlertSeverity;
  message: string;
  status: AlertStatus;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by_name: string | null;
  agent_id: number;
  shift_id: number | null;
  agent_last_name: string;
  agent_first_name: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
