import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoadingContainerComponent } from './loading-container.component';
import { Component } from '@angular/core';

@Component({
  standalone: true,
  imports: [LoadingContainerComponent],
  template: `
    <app-loading-container [loading]="isLoading">
      <p class="projected-content">Content loaded</p>
    </app-loading-container>
  `,
})
class TestHostComponent {
  isLoading = true;
}

describe('LoadingContainerComponent', () => {
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
  });

  it('should show spinner when loading', () => {
    fixture.componentInstance.isLoading = true;
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('mat-spinner')).toBeTruthy();
    expect(el.querySelector('.projected-content')).toBeNull();
  });

  it('should project content when not loading', () => {
    fixture.componentInstance.isLoading = false;
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('mat-spinner')).toBeNull();
    expect(el.querySelector('.projected-content')?.textContent).toContain('Content loaded');
  });

  it('should switch from loading to content', () => {
    fixture.componentInstance.isLoading = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('mat-spinner')).toBeTruthy();

    fixture.componentInstance.isLoading = false;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('mat-spinner')).toBeNull();
    expect(fixture.nativeElement.querySelector('.projected-content')).toBeTruthy();
  });
});
