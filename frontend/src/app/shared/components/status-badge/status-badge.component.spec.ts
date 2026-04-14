import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StatusBadgeComponent } from './status-badge.component';
import { By } from '@angular/platform-browser';

describe('StatusBadgeComponent', () => {
  let fixture: ComponentFixture<StatusBadgeComponent>;
  let component: StatusBadgeComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusBadgeComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(StatusBadgeComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('status', 'pending');
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  const statusCases: { status: string; icon: string; abbreviation: string }[] = [
    { status: 'pending', icon: 'schedule', abbreviation: 'P' },
    { status: 'reviewed', icon: 'visibility', abbreviation: 'R' },
    { status: 'approved', icon: 'check_circle', abbreviation: 'A' },
    { status: 'flagged', icon: 'flag', abbreviation: 'F' },
    { status: 'uncategorized', icon: 'label_off', abbreviation: 'SC' },
  ];

  statusCases.forEach(({ status, icon, abbreviation }) => {
    it(`should render correct icon and abbreviation for "${status}"`, () => {
      fixture.componentRef.setInput('status', status);
      fixture.detectChanges();

      const el = fixture.nativeElement as HTMLElement;
      expect(el.querySelector('mat-icon')?.textContent?.trim()).toBe(icon);
      expect(el.querySelector('.status-badge')?.textContent).toContain(abbreviation);
    });

    it(`should apply "status-${status}" CSS class`, () => {
      fixture.componentRef.setInput('status', status);
      fixture.detectChanges();

      const badge = fixture.debugElement.query(By.css('.status-badge'));
      expect(badge.nativeElement.classList).toContain(`status-${status}`);
    });
  });

  it('should handle unknown status gracefully', () => {
    fixture.componentRef.setInput('status', 'unknown');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('mat-icon')?.textContent?.trim()).toBe('help_outline');
    expect(el.querySelector('.status-badge')?.textContent).toContain('?');
  });
});
