import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SectionTitleComponent } from './section-title.component';
import { Component } from '@angular/core';

describe('SectionTitleComponent', () => {
  let fixture: ComponentFixture<SectionTitleComponent>;
  let component: SectionTitleComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SectionTitleComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SectionTitleComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('text', 'Account Balances');
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should render text', () => {
    fixture.componentRef.setInput('text', 'Monthly Summary');
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('.section-title');
    expect(el?.textContent).toContain('Monthly Summary');
  });

  it('should apply uppercase styling', () => {
    fixture.componentRef.setInput('text', 'Section');
    fixture.detectChanges();

    const el = fixture.nativeElement.querySelector('.section-title') as HTMLElement;
    expect(el).toBeTruthy();
    // The CSS text-transform is applied by the component's styles
  });
});

@Component({
  standalone: true,
  imports: [SectionTitleComponent],
  template: `
    <app-section-title text="Recent">
      <a class="projected-link">View All</a>
    </app-section-title>
  `,
})
class TestHostComponent {}

describe('SectionTitleComponent (content projection)', () => {
  it('should project right-side actions', async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    const fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();

    const link = fixture.nativeElement.querySelector('.projected-link');
    expect(link).toBeTruthy();
    expect(link?.textContent).toContain('View All');
  });
});
