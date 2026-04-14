import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PageHeaderComponent } from './page-header.component';
import { Component } from '@angular/core';

describe('PageHeaderComponent', () => {
  let fixture: ComponentFixture<PageHeaderComponent>;
  let component: PageHeaderComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PageHeaderComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(PageHeaderComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.componentRef.setInput('title', 'Dashboard');
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should render title', () => {
    fixture.componentRef.setInput('title', 'Transactions');
    fixture.detectChanges();

    const h1 = fixture.nativeElement.querySelector('h1');
    expect(h1?.textContent).toContain('Transactions');
  });

  it('should render subtitle when provided', () => {
    fixture.componentRef.setInput('title', 'Dashboard');
    fixture.componentRef.setInput('subtitle', 'April 2026');
    fixture.detectChanges();

    const subtitle = fixture.nativeElement.querySelector('.header-subtitle');
    expect(subtitle?.textContent).toContain('April 2026');
  });

  it('should not render subtitle when not provided', () => {
    fixture.componentRef.setInput('title', 'Dashboard');
    fixture.detectChanges();

    const subtitle = fixture.nativeElement.querySelector('.header-subtitle');
    expect(subtitle).toBeNull();
  });
});

@Component({
  standalone: true,
  imports: [PageHeaderComponent],
  template: `
    <app-page-header title="Test">
      <button class="projected-action">Action</button>
    </app-page-header>
  `,
})
class TestHostComponent {}

describe('PageHeaderComponent (content projection)', () => {
  it('should project action buttons', async () => {
    await TestBed.configureTestingModule({
      imports: [TestHostComponent],
    }).compileComponents();

    const fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('.projected-action');
    expect(button).toBeTruthy();
    expect(button?.textContent).toContain('Action');
  });
});
