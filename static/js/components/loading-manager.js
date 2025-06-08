// Loading Manager - Handles loading states and spinners
export class LoadingManager {
  constructor() {
    this.activeLoaders = new Map();
    this.globalLoader = null;
    this.defaultOptions = {
      overlay: true,
      spinner: 'border',
      size: 'md',
      message: 'Yükleniyor...',
      backdrop: true,
      zIndex: 9999
    };
  }

  // Show global loading overlay
  show(options = {}) {
    const config = { ...this.defaultOptions, ...options };
    
    // Hide existing global loader
    this.hide();

    this.globalLoader = this.createLoader('global', config);
    document.body.appendChild(this.globalLoader);

    // Animate in
    requestAnimationFrame(() => {
      this.globalLoader.classList.add('show');
    });

    return 'global';
  }

  // Hide global loading overlay
  hide() {
    if (this.globalLoader) {
      this.globalLoader.classList.remove('show');
      
      setTimeout(() => {
        if (this.globalLoader && this.globalLoader.parentNode) {
          this.globalLoader.parentNode.removeChild(this.globalLoader);
        }
        this.globalLoader = null;
      }, 300);
    }
  }

  // Show loading on specific element
  showOnElement(element, options = {}) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    if (!targetElement) return null;

    const elementId = targetElement.id || this.generateId();
    const config = {
      ...this.defaultOptions,
      overlay: false,
      backdrop: false,
      ...options
    };

    // Remove existing loader on this element
    this.hideOnElement(targetElement);

    // Make element relative if not already positioned
    const originalPosition = getComputedStyle(targetElement).position;
    if (originalPosition === 'static') {
      targetElement.style.position = 'relative';
      targetElement.dataset.originalPosition = 'static';
    }

    const loader = this.createLoader(elementId, config);
    targetElement.appendChild(loader);

    // Store reference
    this.activeLoaders.set(elementId, {
      element: targetElement,
      loader: loader,
      originalPosition: originalPosition
    });

    // Animate in
    requestAnimationFrame(() => {
      loader.classList.add('show');
    });

    return elementId;
  }

  // Hide loading on specific element
  hideOnElement(element) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    if (!targetElement) return;

    const elementId = targetElement.id || this.findElementId(targetElement);
    const loaderData = this.activeLoaders.get(elementId);

    if (loaderData) {
      const { loader, originalPosition } = loaderData;
      
      loader.classList.remove('show');
      
      setTimeout(() => {
        if (loader && loader.parentNode) {
          loader.parentNode.removeChild(loader);
        }
        
        // Restore original position
        if (originalPosition === 'static') {
          targetElement.style.position = '';
        }
        
        this.activeLoaders.delete(elementId);
      }, 300);
    }
  }

  // Create loader element
  createLoader(id, config) {
    const loader = document.createElement('div');
    loader.className = `loading-overlay ${config.overlay ? 'global-overlay' : 'element-overlay'}`;
    loader.id = `loader-${id}`;
    
    if (config.zIndex) {
      loader.style.zIndex = config.zIndex;
    }

    const spinnerClass = this.getSpinnerClass(config.spinner, config.size);
    const backdropClass = config.backdrop ? 'with-backdrop' : '';

    loader.innerHTML = `
      <div class="loading-content ${backdropClass}">
        <div class="${spinnerClass}" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        ${config.message ? `<div class="loading-message mt-2">${config.message}</div>` : ''}
      </div>
    `;

    return loader;
  }

  // Get spinner CSS classes
  getSpinnerClass(type, size) {
    const sizeClass = size === 'sm' ? 'spinner-border-sm' : '';
    
    switch (type) {
      case 'border':
        return `spinner-border text-primary ${sizeClass}`;
      case 'grow':
        return `spinner-grow text-primary ${sizeClass}`;
      case 'dots':
        return 'loading-dots';
      case 'pulse':
        return 'loading-pulse';
      default:
        return `spinner-border text-primary ${sizeClass}`;
    }
  }

  // Show button loading state
  showButtonLoading(button, options = {}) {
    const targetButton = typeof button === 'string' ? document.querySelector(button) : button;
    if (!targetButton) return;

    const config = {
      text: 'Yükleniyor...',
      spinner: 'border',
      size: 'sm',
      disabled: true,
      ...options
    };

    // Store original state
    targetButton.dataset.originalText = targetButton.innerHTML;
    targetButton.dataset.originalDisabled = targetButton.disabled;

    // Set loading state
    const spinnerClass = this.getSpinnerClass(config.spinner, config.size);
    targetButton.innerHTML = `
      <span class="${spinnerClass} me-2" role="status"></span>
      ${config.text}
    `;
    
    if (config.disabled) {
      targetButton.disabled = true;
    }

    targetButton.classList.add('loading');
  }

  // Hide button loading state
  hideButtonLoading(button) {
    const targetButton = typeof button === 'string' ? document.querySelector(button) : button;
    if (!targetButton) return;

    // Restore original state
    if (targetButton.dataset.originalText) {
      targetButton.innerHTML = targetButton.dataset.originalText;
      delete targetButton.dataset.originalText;
    }

    if (targetButton.dataset.originalDisabled !== undefined) {
      targetButton.disabled = targetButton.dataset.originalDisabled === 'true';
      delete targetButton.dataset.originalDisabled;
    }

    targetButton.classList.remove('loading');
  }

  // Show skeleton loading
  showSkeleton(container, options = {}) {
    const targetContainer = typeof container === 'string' ? document.querySelector(container) : container;
    if (!targetContainer) return;

    const config = {
      rows: 3,
      columns: 1,
      height: '20px',
      borderRadius: '4px',
      ...options
    };

    // Store original content
    targetContainer.dataset.originalContent = targetContainer.innerHTML;

    // Create skeleton
    let skeletonHtml = '<div class="skeleton-container">';
    
    for (let row = 0; row < config.rows; row++) {
      skeletonHtml += '<div class="skeleton-row d-flex gap-2 mb-2">';
      
      for (let col = 0; col < config.columns; col++) {
        const width = Array.isArray(config.width) ? config.width[col] || '100%' : '100%';
        skeletonHtml += `
          <div class="skeleton-item" style="
            height: ${config.height};
            width: ${width};
            border-radius: ${config.borderRadius};
          "></div>
        `;
      }
      
      skeletonHtml += '</div>';
    }
    
    skeletonHtml += '</div>';

    targetContainer.innerHTML = skeletonHtml;
    targetContainer.classList.add('skeleton-loading');
  }

  // Hide skeleton loading
  hideSkeleton(container) {
    const targetContainer = typeof container === 'string' ? document.querySelector(container) : container;
    if (!targetContainer) return;

    // Restore original content
    if (targetContainer.dataset.originalContent) {
      targetContainer.innerHTML = targetContainer.dataset.originalContent;
      delete targetContainer.dataset.originalContent;
    }

    targetContainer.classList.remove('skeleton-loading');
  }

  // Show progress bar
  showProgress(container, options = {}) {
    const targetContainer = typeof container === 'string' ? document.querySelector(container) : container;
    if (!targetContainer) return;

    const config = {
      progress: 0,
      message: '',
      height: '8px',
      animated: true,
      striped: false,
      ...options
    };

    const progressId = this.generateId();
    const animatedClass = config.animated ? 'progress-bar-animated' : '';
    const stripedClass = config.striped ? 'progress-bar-striped' : '';

    const progressHtml = `
      <div class="progress-container" id="progress-${progressId}">
        ${config.message ? `<div class="progress-message mb-2">${config.message}</div>` : ''}
        <div class="progress" style="height: ${config.height};">
          <div class="progress-bar ${animatedClass} ${stripedClass}" 
               role="progressbar" 
               style="width: ${config.progress}%"
               aria-valuenow="${config.progress}" 
               aria-valuemin="0" 
               aria-valuemax="100">
          </div>
        </div>
      </div>
    `;

    targetContainer.innerHTML = progressHtml;
    return progressId;
  }

  // Update progress bar
  updateProgress(progressId, progress, message = null) {
    const progressContainer = document.getElementById(`progress-${progressId}`);
    if (!progressContainer) return;

    const progressBar = progressContainer.querySelector('.progress-bar');
    const messageElement = progressContainer.querySelector('.progress-message');

    if (progressBar) {
      progressBar.style.width = `${progress}%`;
      progressBar.setAttribute('aria-valuenow', progress);
    }

    if (message && messageElement) {
      messageElement.textContent = message;
    }
  }

  // Find element ID for active loaders
  findElementId(element) {
    for (const [id, data] of this.activeLoaders) {
      if (data.element === element) {
        return id;
      }
    }
    return null;
  }

  // Generate unique ID
  generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  // Check if loading is active
  isLoading(elementOrId = null) {
    if (elementOrId === null) {
      return this.globalLoader !== null;
    }

    if (typeof elementOrId === 'string') {
      return this.activeLoaders.has(elementOrId);
    }

    return this.findElementId(elementOrId) !== null;
  }

  // Hide all loaders
  hideAll() {
    // Hide global loader
    this.hide();

    // Hide all element loaders
    this.activeLoaders.forEach((data, id) => {
      this.hideOnElement(data.element);
    });
  }

  // Destroy loading manager
  destroy() {
    this.hideAll();
    this.activeLoaders.clear();
  }
}
