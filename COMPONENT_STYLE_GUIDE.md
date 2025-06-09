# Component Style Guide
## Arsa Analiz ve Sunum Platformu

### 🎨 Design System Overview

This style guide provides examples and usage guidelines for the unified design system components.

### 🎯 Color System

#### Primary Colors
```css
--primary-color: #2563eb;      /* Main brand blue */
--primary-hover: #1d4ed8;      /* Hover state */
--primary-light: #dbeafe;      /* Light variant */
--primary-dark: #1e40af;       /* Dark variant */
```

#### Status Colors
```css
--success-color: #059669;      /* Success green */
--warning-color: #d97706;      /* Warning amber */
--error-color: #dc2626;        /* Error red */
--info-color: #0284c7;         /* Info blue */
```

#### Neutral Colors
```css
--text-primary: #111827;       /* Main text */
--text-secondary: #6b7280;     /* Secondary text */
--text-muted: #9ca3af;         /* Muted text */
--bg-primary: #ffffff;         /* Main background */
--bg-secondary: #f9fafb;       /* Secondary background */
--border-color: #e5e7eb;       /* Border color */
```

### 🔘 Buttons

#### Primary Button
```html
<button class="btn btn-primary">
  <i class="fas fa-plus me-2"></i>Primary Action
</button>
```

#### Secondary Button
```html
<button class="btn btn-secondary">
  <i class="fas fa-edit me-2"></i>Secondary Action
</button>
```

#### Outline Button
```html
<button class="btn btn-outline-primary">
  <i class="fas fa-download me-2"></i>Outline Action
</button>
```

#### Button Sizes
```html
<!-- Small -->
<button class="btn btn-primary btn-sm">Small Button</button>

<!-- Default -->
<button class="btn btn-primary">Default Button</button>

<!-- Large -->
<button class="btn btn-primary btn-lg">Large Button</button>
```

### 📋 Cards

#### Basic Card
```html
<div class="card">
  <div class="card-header">
    <h5 class="card-title">Card Title</h5>
  </div>
  <div class="card-body">
    <p class="card-text">Card content goes here.</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary">Action</button>
  </div>
</div>
```

#### Stat Card
```html
<div class="card stat-card">
  <div class="card-body">
    <div class="d-flex align-items-center">
      <div class="stat-icon bg-primary text-white me-3">
        <i class="fas fa-chart-line"></i>
      </div>
      <div>
        <h6 class="text-muted mb-1">Total Analyses</h6>
        <h3 class="mb-0 fw-bold">1,234</h3>
      </div>
    </div>
  </div>
</div>
```

#### Quick Access Card
```html
<a href="#" class="quick-access-card text-decoration-none">
  <div class="card-body text-center p-4">
    <i class="fas fa-plus-circle text-primary mb-3" style="font-size: 2.5rem;"></i>
    <h6 class="fw-medium">New Analysis</h6>
  </div>
</a>
```

### 📝 Forms

#### Form Group
```html
<div class="mb-3">
  <label for="email" class="form-label">
    <i class="fas fa-envelope me-2"></i>Email Address
  </label>
  <input type="email" class="form-control" id="email" placeholder="Enter email">
  <div class="form-text">We'll never share your email with anyone else.</div>
</div>
```

#### Input Group
```html
<div class="input-group mb-3">
  <span class="input-group-text">
    <i class="fas fa-search"></i>
  </span>
  <input type="text" class="form-control" placeholder="Search...">
  <button class="btn btn-outline-secondary" type="button">
    <i class="fas fa-times"></i>
  </button>
</div>
```

#### Form Validation
```html
<div class="mb-3">
  <label for="validationExample" class="form-label">Required Field</label>
  <input type="text" class="form-control is-invalid" id="validationExample">
  <div class="invalid-feedback">
    Please provide a valid input.
  </div>
</div>
```

### 📊 Tables

#### Basic Table
```html
<div class="table-responsive">
  <table class="table table-hover">
    <thead>
      <tr>
        <th>Name</th>
        <th>Email</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>John Doe</td>
        <td>john@example.com</td>
        <td><span class="badge bg-success">Active</span></td>
        <td>
          <button class="btn btn-sm btn-outline-primary">Edit</button>
          <button class="btn btn-sm btn-outline-danger">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### 🚨 Alerts

#### Alert Types
```html
<!-- Success Alert -->
<div class="alert alert-success" role="alert">
  <i class="fas fa-check-circle me-2"></i>
  <strong>Success!</strong> Your action was completed successfully.
</div>

<!-- Warning Alert -->
<div class="alert alert-warning" role="alert">
  <i class="fas fa-exclamation-triangle me-2"></i>
  <strong>Warning!</strong> Please check your input.
</div>

<!-- Error Alert -->
<div class="alert alert-danger" role="alert">
  <i class="fas fa-times-circle me-2"></i>
  <strong>Error!</strong> Something went wrong.
</div>

<!-- Info Alert -->
<div class="alert alert-info" role="alert">
  <i class="fas fa-info-circle me-2"></i>
  <strong>Info!</strong> Here's some helpful information.
</div>
```

### 🏷️ Badges

#### Badge Variants
```html
<span class="badge bg-primary">Primary</span>
<span class="badge bg-secondary">Secondary</span>
<span class="badge bg-success">Success</span>
<span class="badge bg-warning">Warning</span>
<span class="badge bg-danger">Danger</span>
<span class="badge bg-info">Info</span>
```

### 🗂️ Navigation

#### Navbar
```html
<nav class="navbar navbar-expand-lg">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">
      <i class="fas fa-chart-line me-2"></i>Arsa Analiz
    </a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link active" href="#">Home</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#">Analysis</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#">CRM</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
```

#### Sidebar Navigation
```html
<nav class="sidebar">
  <div class="sidebar-header">
    <h5 class="sidebar-title">Navigation</h5>
  </div>
  <div class="sidebar-nav">
    <a href="#" class="nav-link active">
      <i class="fas fa-home me-2"></i>Dashboard
    </a>
    <a href="#" class="nav-link">
      <i class="fas fa-chart-line me-2"></i>Analytics
    </a>
    <a href="#" class="nav-link">
      <i class="fas fa-users me-2"></i>CRM
    </a>
  </div>
</nav>
```

### 🪟 Modals

#### Basic Modal
```html
<div class="modal fade" id="exampleModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Modal Title</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p>Modal content goes here.</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        <button type="button" class="btn btn-primary">Save changes</button>
      </div>
    </div>
  </div>
</div>
```

### 📱 Responsive Utilities

#### Responsive Display
```html
<!-- Hide on mobile -->
<div class="d-none d-md-block">Hidden on mobile</div>

<!-- Show only on mobile -->
<div class="d-block d-md-none">Visible only on mobile</div>

<!-- Responsive text alignment -->
<div class="text-center text-md-start">Centered on mobile, left on desktop</div>
```

#### Responsive Grid
```html
<div class="row">
  <div class="col-12 col-md-6 col-lg-4">
    <!-- Full width on mobile, half on tablet, third on desktop -->
  </div>
  <div class="col-12 col-md-6 col-lg-4">
    <!-- Responsive column -->
  </div>
  <div class="col-12 col-md-12 col-lg-4">
    <!-- Full width on mobile and tablet, third on desktop -->
  </div>
</div>
```

### 🎭 Theme Support

#### CSS Custom Properties Usage
```css
/* Use theme variables in custom CSS */
.custom-component {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}
```

#### Theme Toggle Implementation
```html
<button id="theme-toggle" class="btn btn-outline-secondary">
  <i class="fas fa-moon" id="theme-icon"></i>
  <span id="theme-text">Dark Mode</span>
</button>
```

### 📏 Spacing System

#### Margin and Padding Classes
```html
<!-- Margin -->
<div class="m-3">Margin all sides</div>
<div class="mt-2 mb-4">Margin top and bottom</div>
<div class="mx-auto">Centered horizontally</div>

<!-- Padding -->
<div class="p-4">Padding all sides</div>
<div class="px-3 py-2">Padding horizontal and vertical</div>
```

### 🔧 Utility Classes

#### Text Utilities
```html
<p class="text-primary">Primary text color</p>
<p class="text-muted">Muted text color</p>
<p class="fw-bold">Bold text</p>
<p class="text-center">Centered text</p>
```

#### Background Utilities
```html
<div class="bg-primary-light p-3">Light primary background</div>
<div class="bg-success-light p-3">Light success background</div>
```

---

*This style guide ensures consistent implementation of the design system across all components and pages.*
