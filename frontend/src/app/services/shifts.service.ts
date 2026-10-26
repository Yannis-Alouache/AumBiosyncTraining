import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Paginated, Shift } from '../core/models';
import { toQueryParams } from './agents.service';

export interface ShiftFilters {
  site_id?: number | null;
  agent_id?: number | null;
  status?: string | null;
  from?: string | null;
  to?: string | null;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class ShiftsService {
  private readonly http = inject(HttpClient);

  list(filters: ShiftFilters = {}): Observable<Paginated<Shift>> {
    return this.http.get<Paginated<Shift>>('/api/shifts', { params: toQueryParams(filters) });
  }
}
