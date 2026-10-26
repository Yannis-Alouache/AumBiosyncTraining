import { BreakpointObserver } from '@angular/cdk/layout';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { map } from 'rxjs';

import { User } from '../core/models';
import { AuthService } from '../core/auth.service';
import { roleLabel } from '../shared/fatigue';

interface NavLink {
  path: string;
  label: string;
  icon: string;
}

/** Application shell: side navigation, top bar, content area. */
@Component({
  selector: 'app-shell',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatTooltipModule,
  ],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Shell {
  private readonly breakpointObserver = inject(BreakpointObserver);

  readonly auth = inject(AuthService);
  readonly mobileOpen = signal(false);
  readonly isMobile = toSignal(
    this.breakpointObserver.observe('(max-width: 960px)').pipe(map((state) => state.matches)),
    { initialValue: false },
  );

  readonly user = computed<User | null>(() => this.auth.user());
  readonly initials = computed(() => {
    const u = this.user();
    if (!u) {
      return '?';
    }
    return `${u.first_name.charAt(0)}${u.last_name.charAt(0)}`.toUpperCase();
  });
  readonly userRoleLabel = computed(() => {
    const u = this.user();
    return u ? roleLabel(u.role) : '';
  });

  readonly links: NavLink[] = [
    { path: '/agents', label: 'Agents', icon: 'groups' },
    { path: '/alerts', label: 'Alertes', icon: 'notifications' },
  ];

  logout(): void {
    this.auth.logout();
  }
}
