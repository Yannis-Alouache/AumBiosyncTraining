import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** Composed empty state: icon, title, action hint. */
@Component({
  selector: 'app-empty-state',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="empty-state">
      <span class="material-icons">{{ icon() }}</span>
      <div class="title">{{ title() }}</div>
      @if (message()) {
        <p class="message">{{ message() }}</p>
      }
      <ng-content />
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 44px 20px;
        text-align: center;
        color: var(--mat-sys-on-surface-variant);
      }
      .material-icons {
        font-size: 34px;
        opacity: 0.55;
      }
      .title {
        font-weight: 700;
        color: var(--mat-sys-on-surface);
      }
      .message {
        margin: 0;
        max-width: 46ch;
        font-size: 13.5px;
      }
    `,
  ],
})
export class EmptyState {
  readonly icon = input.required<string>();
  readonly title = input.required<string>();
  readonly message = input<string>('');
}
