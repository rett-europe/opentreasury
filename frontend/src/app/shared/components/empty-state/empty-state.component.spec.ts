import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EmptyStateComponent } from './empty-state.component';

describe('EmptyStateComponent', () => {
  let fixture: ComponentFixture<EmptyStateComponent>;
  let component: EmptyStateComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmptyStateComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(EmptyStateComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('icon', 'receipt_long');
    fixture.componentRef.setInput('message', 'No transactions found');
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should render icon and message', () => {
    fixture.componentRef.setInput('icon', 'receipt_long');
    fixture.componentRef.setInput('message', 'No data available');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('mat-icon')?.textContent?.trim()).toBe('receipt_long');
    expect(el.querySelector('p')?.textContent).toContain('No data available');
  });

  it('should not show action button when actionLabel is not provided', () => {
    fixture.componentRef.setInput('icon', 'info');
    fixture.componentRef.setInput('message', 'Empty');
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button).toBeNull();
  });

  it('should show action button when actionLabel is provided', () => {
    fixture.componentRef.setInput('icon', 'info');
    fixture.componentRef.setInput('message', 'Empty');
    fixture.componentRef.setInput('actionLabel', 'Add Item');
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button).toBeTruthy();
    expect(button?.textContent).toContain('Add Item');
  });

  it('should emit action event when button clicked', () => {
    fixture.componentRef.setInput('icon', 'info');
    fixture.componentRef.setInput('message', 'Empty');
    fixture.componentRef.setInput('actionLabel', 'Add Item');
    fixture.detectChanges();

    const spy = jest.fn();
    component.action.subscribe(spy);

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    button.click();

    expect(spy).toHaveBeenCalledTimes(1);
  });
});
