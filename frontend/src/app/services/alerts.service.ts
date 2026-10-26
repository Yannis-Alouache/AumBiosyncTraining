import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Alert } from '../core/models';
import { toQueryParams } from './agents.service';

export interface AlertFilters {
  severity?: string | null;
  status?: string | null;
  agent_id?: number | null;
  limit?: number;
}

@Injectable({ providedIn: 'root' })
export class AlertsService {
  private readonly http = inject(HttpClient);

  list(filters: AlertFilters = {}): Observable<{ items: Alert[]; total: number }> {
    return this.http.get<{ items: Alert[]; total: number }>('/api/alerts', {
      params: toQueryParams(filters),
    });
  }
}
