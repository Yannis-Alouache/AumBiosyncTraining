import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Site } from '../core/models';

@Injectable({ providedIn: 'root' })
export class SitesService {
  private readonly http = inject(HttpClient);

  list(): Observable<{ items: Site[] }> {
    return this.http.get<{ items: Site[] }>('/api/sites');
  }
}
