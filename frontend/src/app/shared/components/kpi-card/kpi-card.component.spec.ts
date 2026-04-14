import { ComponentFixture, TestBed } from '@angular/core/testing';
import { KpiCardComponent } from './kpi-card.component';
import { By } from '@angular/platform-browser';

describe('KpiCardComponent', () => {
  let fixture: ComponentFixture<KpiCardComponent>;
  let component: KpiCardComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [KpiCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(KpiCardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('label', 'Income');
    fixture.componentRef.setInput('value', '€1,200.00');
    fixture.componentRef.setInput('icon', 'arrow_upward');
    fixture.componentRef.setInput('colorClass', 'income');
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should render label, value, and icon', () => {
    fixture.componentRef.setInput('label', 'Total Income');
    fixture.componentRef.setInput('value', '€5,000.00');
    fixture.componentRef.setInput('icon', 'arrow_upward');
    fixture.componentRef.setInput('colorClass', 'income');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.kpi-label')?.textContent).toContain('Total Income');
    expect(el.querySelector('.kpi-value')?.textContent).toContain('€5,000.00');
    expect(el.querySelector('mat-icon')?.textContent?.trim()).toBe('arrow_upward');
  });

  it('should apply colorClass as CSS class', () => {
    fixture.componentRef.setInput('label', 'Expenses');
    fixture.componentRef.setInput('value', '€800.00');
    fixture.componentRef.setInput('icon', 'arrow_downward');
    fixture.componentRef.setInput('colorClass', 'expense');
    fixture.detectChanges();

    const card = fixture.debugElement.query(By.css('.kpi-card'));
    expect(card.nativeElement.classList).toContain('kpi-expense');
  });

  it('should apply different colorClass for net', () => {
    fixture.componentRef.setInput('label', 'Net');
    fixture.componentRef.setInput('value', '€400.00');
    fixture.componentRef.setInput('icon', 'account_balance');
    fixture.componentRef.setInput('colorClass', 'net');
    fixture.detectChanges();

    const card = fixture.debugElement.query(By.css('.kpi-card'));
    expect(card.nativeElement.classList).toContain('kpi-net');
  });
});
