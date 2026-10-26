import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Agent } from '../core/models';

export interface AgentFilters {
  q?: string;
  site_id?: number | null;
  status?: string | null;
}

@Injectable({ providedIn: 'root' })
export class AgentsService {
  private readonly http = inject(HttpClient);

  list(filters: AgentFilters = {}): Observable<{ items: Agent[]; total: number }> {
    return this.http.get<{ items: Agent[]; total: number }>('/api/agents', {
      params: toQueryParams(filters),
    });
  }
}

export function toQueryParams(filters: object): HttpParams {
  let params = new HttpParams();
  for (const [key, value] of Object.entries(filters as Record<string, unknown>)) {
    if (value !== null && value !== undefined && value !== '') {
      params = params.set(key, String(value));
    }
  }
  return params;
}
