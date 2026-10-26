import { DecimalPipe } from '@angular/common';
import { AfterViewInit, ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';

import { Agent, Site } from '../../core/models';
import { AgentsService } from '../../services/agents.service';
import { SitesService } from '../../services/sites.service';
import { EmptyState } from '../../shared/empty-state';
import { agentStatusClass, agentStatusLabel, fatigueLabel, fatigueLevel } from '../../shared/fatigue';

/** Agents registry: search, site and status filters, local sorting. */
@Component({
  selector: 'app-agents-list',
  imports: [
    DecimalPipe,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatSortModule,
    MatTableModule,
    EmptyState,
  ],
  templateUrl: './agents-list.html',
  styleUrl: './agents-list.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AgentsListPage implements OnInit, AfterViewInit, OnDestroy {
  private readonly agentsService = inject(AgentsService);
  private readonly sitesService = inject(SitesService);
  private readonly destroy = new Subject<void>();

  @ViewChild(MatSort) sort?: MatSort;

  readonly columns = ['agent', 'position', 'site', 'status', 'fatigue'];
  readonly dataSource = new MatTableDataSource<Agent>([]);
  readonly total = signal(0);
  readonly loading = signal(true);
  readonly hasError = signal(false);
  readonly sites = signal<Site[]>([]);
  readonly statuses = ['ACTIVE', 'LEAVE', 'TRAINING', 'SUSPENDED'];

  search = '';
  siteId: number | null = null;
  statusFilter: string | null = null;

  private readonly searchTerms = new Subject<string>();

  ngOnInit(): void {
    this.sitesService.list().subscribe({
      next: (response) => this.sites.set(response.items),
      error: () => this.sites.set([]),
    });
    this.searchTerms
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy))
      .subscribe((value) => {
        this.search = value;
        this.load();
      });
    this.load();
  }

  ngAfterViewInit(): void {
    this.dataSource.sort = this.sort ?? null;
    this.dataSource.sortingDataAccessor = (agent, column) => {
      switch (column) {
        case 'agent':
          return agent.last_name;
        case 'fatigue':
          return agent.fatigue_index;
        case 'site':
          return agent.site_name;
        default:
          return agent.status;
      }
    };
  }

  ngOnDestroy(): void {
    this.destroy.next();
    this.destroy.complete();
  }

  onSearch(value: string): void {
    this.searchTerms.next(value);
  }

  onFilterChange(): void {
    this.load();
  }

  resetFilters(): void {
    this.search = '';
    this.siteId = null;
    this.statusFilter = null;
    this.load();
  }

  get hasActiveFilters(): boolean {
    return this.search !== '' || this.siteId !== null || this.statusFilter !== null;
  }

  load(): void {
    this.loading.set(true);
    this.hasError.set(false);
    this.agentsService
      .list({ q: this.search, site_id: this.siteId, status: this.statusFilter })
      .subscribe({
        next: (response) => {
          this.dataSource.data = response.items;
          this.total.set(response.total);
          this.loading.set(false);
        },
        error: () => {
          this.hasError.set(true);
          this.loading.set(false);
        },
      });
  }

  initials(agent: Agent): string {
    return `${agent.first_name.charAt(0)}${agent.last_name.charAt(0)}`.toUpperCase();
  }

  fatigueClass(index: number): string {
    return fatigueLevel(index);
  }

  fatigueLevelLabel(index: number): string {
    return fatigueLabel(index);
  }

  statusLabel = agentStatusLabel;
  statusClass = agentStatusClass;
}
