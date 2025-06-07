// Form Validator - Handles form validation and user feedback
export class FormValidator {
  constructor() {
    this.forms = new Map();
    this.rules = new Map();
    this.messages = {
      required: 'Bu alan zorunludur',
      email: 'Geçerli bir e-posta adresi giriniz',
      min: 'Minimum {min} karakter olmalıdır',
      max: 'Maksimum {max} karakter olmalıdır',
      pattern: 'Geçersiz format',
      number: 'Geçerli bir sayı giriniz',
      url: 'Geçerli bir URL giriniz',
      tel: 'Geçerli bir telefon numarası giriniz',
      date: 'Geçerli bir tarih giriniz',
      match: 'Alanlar eşleşmiyor'
    };
    
    this.init();
  }

  // Initialize form validation
  init() {
    this.bindEvents();
    this.initForms();
  }

  // Initialize all forms with validation
  initForms() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => this.addForm(form));
  }

  // Bind global events
  bindEvents() {
    // Real-time validation on input
    document.addEventListener('input', (e) => {
      if (e.target.hasAttribute('data-validate')) {
        this.validateField(e.target);
      }
    });

    // Validation on blur
    document.addEventListener('blur', (e) => {
      if (e.target.hasAttribute('data-validate')) {
        this.validateField(e.target);
      }
    }, true);

    // Form submission validation
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (form.hasAttribute('data-validate')) {
        if (!this.validateForm(form)) {
          e.preventDefault();
          e.stopPropagation();
        }
      }
    });
  }

  // Add form to validation system
  addForm(form, options = {}) {
    const formId = form.id || this.generateId();
    if (!form.id) form.id = formId;

    const config = {
      realTime: true,
      showErrors: true,
      scrollToError: true,
      ...options
    };

    this.forms.set(formId, {
      element: form,
      config: config,
      fields: new Map()
    });

    // Initialize form fields
    this.initFormFields(form);
    
    return formId;
  }

  // Initialize form fields
  initFormFields(form) {
    const fields = form.querySelectorAll('[data-validate]');
    fields.forEach(field => {
      this.addField(field);
    });
  }

  // Add field validation rules
  addField(field, rules = null) {
    const fieldRules = rules || this.parseFieldRules(field);
    const fieldId = field.name || field.id || this.generateId();
    
    this.rules.set(fieldId, fieldRules);
    
    // Add visual feedback elements
    this.addFieldFeedback(field);
  }

  // Parse validation rules from data attributes
  parseFieldRules(field) {
    const rules = [];
    const validateAttr = field.getAttribute('data-validate');
    
    if (validateAttr) {
      const ruleStrings = validateAttr.split('|');
      
      ruleStrings.forEach(ruleString => {
        const [ruleName, ...params] = ruleString.split(':');
        const rule = {
          name: ruleName.trim(),
          params: params.length > 0 ? params.join(':').split(',') : []
        };
        rules.push(rule);
      });
    }

    return rules;
  }

  // Add visual feedback elements to field
  addFieldFeedback(field) {
    // Skip if feedback already exists
    if (field.parentNode.querySelector('.invalid-feedback')) {
      return;
    }

    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    
    // Insert after the field
    field.parentNode.insertBefore(feedback, field.nextSibling);
  }

  // Validate single field
  validateField(field) {
    const fieldId = field.name || field.id;
    const rules = this.rules.get(fieldId);
    
    if (!rules) return true;

    const value = this.getFieldValue(field);
    const errors = [];

    // Check each rule
    for (const rule of rules) {
      const isValid = this.checkRule(value, rule, field);
      if (!isValid) {
        const message = this.getErrorMessage(rule, field);
        errors.push(message);
        break; // Stop at first error
      }
    }

    // Update field UI
    this.updateFieldUI(field, errors);
    
    return errors.length === 0;
  }

  // Validate entire form
  validateForm(form) {
    const fields = form.querySelectorAll('[data-validate]');
    let isValid = true;
    let firstErrorField = null;

    fields.forEach(field => {
      const fieldValid = this.validateField(field);
      if (!fieldValid && !firstErrorField) {
        firstErrorField = field;
      }
      isValid = isValid && fieldValid;
    });

    // Scroll to first error
    if (!isValid && firstErrorField) {
      this.scrollToField(firstErrorField);
      firstErrorField.focus();
    }

    return isValid;
  }

  // Check individual validation rule
  checkRule(value, rule, field) {
    switch (rule.name) {
      case 'required':
        return value.trim() !== '';
        
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return !value || emailRegex.test(value);
        
      case 'min':
        const minLength = parseInt(rule.params[0]);
        return !value || value.length >= minLength;
        
      case 'max':
        const maxLength = parseInt(rule.params[0]);
        return !value || value.length <= maxLength;
        
      case 'pattern':
        const pattern = new RegExp(rule.params[0]);
        return !value || pattern.test(value);
        
      case 'number':
        return !value || !isNaN(value) && !isNaN(parseFloat(value));
        
      case 'url':
        try {
          new URL(value);
          return true;
        } catch {
          return !value;
        }
        
      case 'tel':
        const telRegex = /^[\+]?[0-9\s\-\(\)]+$/;
        return !value || telRegex.test(value);
        
      case 'date':
        return !value || !isNaN(Date.parse(value));
        
      case 'match':
        const matchField = document.querySelector(`[name="${rule.params[0]}"]`);
        return !value || !matchField || value === this.getFieldValue(matchField);
        
      case 'custom':
        // Custom validation function
        const customFn = window[rule.params[0]];
        return typeof customFn === 'function' ? customFn(value, field) : true;
        
      default:
        return true;
    }
  }

  // Get field value
  getFieldValue(field) {
    if (field.type === 'checkbox' || field.type === 'radio') {
      return field.checked ? field.value : '';
    }
    return field.value || '';
  }

  // Get error message for rule
  getErrorMessage(rule, field) {
    const customMessage = field.getAttribute(`data-${rule.name}-message`);
    if (customMessage) {
      return customMessage;
    }

    let message = this.messages[rule.name] || 'Geçersiz değer';
    
    // Replace placeholders
    rule.params.forEach((param, index) => {
      message = message.replace(`{${rule.name}}`, param);
      message = message.replace(`{${index}}`, param);
    });

    return message;
  }

  // Update field UI with validation state
  updateFieldUI(field, errors) {
    const isValid = errors.length === 0;
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    
    // Update field classes
    field.classList.remove('is-valid', 'is-invalid');
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // Update feedback message
    if (feedback) {
      feedback.textContent = errors.length > 0 ? errors[0] : '';
      feedback.style.display = errors.length > 0 ? 'block' : 'none';
    }
  }

  // Scroll to field
  scrollToField(field) {
    const offset = 100; // Offset from top
    const fieldTop = field.getBoundingClientRect().top + window.pageYOffset - offset;
    
    window.scrollTo({
      top: fieldTop,
      behavior: 'smooth'
    });
  }

  // Add custom validation rule
  addRule(name, validator, message) {
    this.messages[name] = message;
    
    // Store custom validator if it's a function
    if (typeof validator === 'function') {
      window[`validate_${name}`] = validator;
    }
  }

  // Remove validation from form
  removeForm(formId) {
    const formData = this.forms.get(formId);
    if (formData) {
      const { element } = formData;
      
      // Remove validation classes and feedback
      const fields = element.querySelectorAll('[data-validate]');
      fields.forEach(field => {
        field.classList.remove('is-valid', 'is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
          feedback.remove();
        }
      });
      
      this.forms.delete(formId);
    }
  }

  // Reset form validation state
  resetForm(form) {
    const targetForm = typeof form === 'string' ? document.getElementById(form) : form;
    if (!targetForm) return;

    const fields = targetForm.querySelectorAll('[data-validate]');
    fields.forEach(field => {
      field.classList.remove('is-valid', 'is-invalid');
      const feedback = field.parentNode.querySelector('.invalid-feedback');
      if (feedback) {
        feedback.textContent = '';
        feedback.style.display = 'none';
      }
    });
  }

  // Show field error manually
  showFieldError(field, message) {
    const targetField = typeof field === 'string' ? document.querySelector(`[name="${field}"]`) : field;
    if (!targetField) return;

    this.updateFieldUI(targetField, [message]);
  }

  // Clear field error
  clearFieldError(field) {
    const targetField = typeof field === 'string' ? document.querySelector(`[name="${field}"]`) : field;
    if (!targetField) return;

    this.updateFieldUI(targetField, []);
  }

  // Generate unique ID
  generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  // Destroy validator
  destroy() {
    this.forms.clear();
    this.rules.clear();
  }
}
