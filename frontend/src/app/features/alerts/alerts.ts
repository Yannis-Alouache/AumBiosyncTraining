import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';

import { Alert } from '../../core/models';
import { AlertsService } from '../../services/alerts.service';
import { EmptyState } from '../../shared/empty-state';
import {
  alertStatusLabel,
  alertTypeLabel,
  severityClass,
} from '../../shared/fatigue';

/** Alert center: filtered consultation (read-only in this version). */
@Component({
  selector: 'app-alerts',
  imports: [
    DatePipe,
    MatButtonToggleModule,
    MatFormFieldModule,
    MatSelectModule,
    MatTableModule,
    EmptyState,
  ],
  templateUrl: './alerts.html',
  styleUrl: './alerts.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertsPage implements OnInit {
  private readonly alertsService = inject(AlertsService);

  readonly columns = ['severity', 'detail', 'agent', 'date', 'status'];
  readonly alerts = signal<Alert[]>([]);
  readonly total = signal(0);
  readonly loading = signal(true);
  readonly hasError = signal(false);

  readonly statusFilter = signal<string | null>('NEW');
  readonly severityFilter = signal<string | null>(null);

  readonly statusChoices = [
    { value: null as string | null, label: 'Toutes' },
    { value: 'NEW' as string | null, label: 'Nouvelles' },
    { value: 'ACKNOWLEDGED' as string | null, label: 'Acquittées' },
    { value: 'RESOLVED' as string | null, label: 'Résolues' },
  ];
  readonly severities = ['INFO', 'WARNING', 'CRITICAL'];

  ngOnInit(): void {
    this.load();
  }

  onStatusChange(value: string | null): void {
    this.statusFilter.set(value);
    this.load();
  }

  onSeverityChange(value: string | null): void {
    this.severityFilter.set(value);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.hasError.set(false);
    this.alertsService
      .list({ status: this.statusFilter(), severity: this.severityFilter(), limit: 200 })
      .subscribe({
        next: (response) => {
          this.alerts.set(response.items);
          this.total.set(response.total);
          this.loading.set(false);
        },
        error: () => {
          this.hasError.set(true);
          this.loading.set(false);
        },
      });
  }

  typeLabel = alertTypeLabel;
  statusLabel = alertStatusLabel;
  severityBadgeClass = severityClass;
}
