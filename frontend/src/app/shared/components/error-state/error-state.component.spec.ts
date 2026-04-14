import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ErrorStateComponent } from './error-state.component';

describe('ErrorStateComponent', () => {
  let fixture: ComponentFixture<ErrorStateComponent>;
  let component: ErrorStateComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ErrorStateComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ErrorStateComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('message', 'Something went wrong');
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should render error icon and message', () => {
    fixture.componentRef.setInput('message', 'Failed to load data');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('mat-icon')?.textContent?.trim()).toBe('error_outline');
    expect(el.querySelector('p')?.textContent).toContain('Failed to load data');
  });

  it('should not show retry button when retryLabel is not provided', () => {
    fixture.componentRef.setInput('message', 'Error');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('button')).toBeNull();
  });

  it('should show retry button when retryLabel is provided', () => {
    fixture.componentRef.setInput('message', 'Error');
    fixture.componentRef.setInput('retryLabel', 'Try Again');
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button).toBeTruthy();
    expect(button?.textContent).toContain('Try Again');
  });

  it('should emit retry event when button clicked', () => {
    fixture.componentRef.setInput('message', 'Error');
    fixture.componentRef.setInput('retryLabel', 'Reintentar');
    fixture.detectChanges();

    const spy = jest.fn();
    component.retry.subscribe(spy);

    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;
    button.click();

    expect(spy).toHaveBeenCalledTimes(1);
  });
});
