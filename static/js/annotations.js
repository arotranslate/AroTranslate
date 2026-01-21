/**
 * Annotation Manager - State-Based Approach
 * Handles text selection, highlighting, and error annotation management
 *
 * Key Design: Instead of manipulating DOM ranges directly, we:
 * 1. Store plain text separately from annotations
 * 2. Store annotations as position data [{start, end, level}]
 * 3. Re-render the entire content when changes occur
 */

class AnnotationManager {
  constructor(config) {
    this.targetElementId = config.targetElementId || 'outputText';
    this.menuSelector = config.menuSelector || '.error-right-click-menu';
    this.plainText = '';              // The original text without HTML
    this.annotations = [];            // Array of {start, end, level}
    this.pendingSelection = null;     // Selection waiting for menu action
    this.onChangeCallback = config.onChange || null;
    this.initialAnnotations = config.initialAnnotations || [];

    this.init();
  }

  /**
   * Initialize the manager
   */
  init() {
    const container = document.getElementById(this.targetElementId);
    if (!container) {
      console.error(`AnnotationManager: Element #${this.targetElementId} not found`);
      return;
    }

    // Store the plain text content
    this.plainText = container.textContent;

    // Load initial annotations if provided
    if (this.initialAnnotations.length > 0) {
      this.annotations = [...this.initialAnnotations];
      this.render();
    }

    this.setupEventListeners();
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    this.setupSelectionTracking();
    this.setupContextMenu();
    this.setupMenuHandlers();
  }

  /**
   * Track text selection and convert to character positions
   */
  setupSelectionTracking() {
    const container = document.getElementById(this.targetElementId);

    container.addEventListener('mouseup', () => {
      this.captureSelection();
    });

    container.addEventListener('keyup', () => {
      this.captureSelection();
    });
  }

  /**
   * Capture the current selection and convert to character positions
   */
  captureSelection() {
    const selection = window.getSelection();

    if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
      this.pendingSelection = null;
      return;
    }

    const container = document.getElementById(this.targetElementId);
    const range = selection.getRangeAt(0);

    // Check if selection is within our container
    if (!container.contains(range.commonAncestorContainer)) {
      this.pendingSelection = null;
      return;
    }

    // Convert DOM range to character positions
    const positions = this.rangeToCharPositions(range, container);
    if (positions && positions.start <= positions.end) {
      this.pendingSelection = positions;
    } else {
      this.pendingSelection = null;
    }
  }

  /**
   * Convert a DOM Range to character positions relative to plain text
   */
  rangeToCharPositions(range, container) {
    try {
      // Create a range from start of container to selection start
      const preRange = document.createRange();
      preRange.selectNodeContents(container);
      preRange.setEnd(range.startContainer, range.startOffset);

      const start = preRange.toString().length;
      const selectedText = range.toString();
      const end = start + selectedText.length - 1;

      // Validate positions
      if (start < 0 || end < start || end >= this.plainText.length) {
        return null;
      }

      return { start, end };
    } catch (e) {
      console.error('Error calculating positions:', e);
      return null;
    }
  }

  /**
   * Setup context menu (right-click)
   */
  setupContextMenu() {
    const container = document.getElementById(this.targetElementId);
    const menu = document.querySelector(this.menuSelector);

    if (!menu) {
      console.error(`AnnotationManager: Menu ${this.menuSelector} not found`);
      return;
    }

    container.addEventListener('contextmenu', (event) => {
      event.preventDefault();

      // Capture selection before showing menu (in case it gets lost)
      this.captureSelection();

      // Position and show menu
      menu.style.display = 'block';
      menu.style.top = event.pageY + 'px';
      menu.style.left = event.pageX + 'px';
    });

    // Hide menu when clicking outside
    document.addEventListener('mousedown', (e) => {
      if (!e.target.closest(this.menuSelector)) {
        menu.style.display = 'none';
      }
    });
  }

  /**
   * Setup menu item click handlers
   */
  setupMenuHandlers() {
    const menu = document.querySelector(this.menuSelector);
    if (!menu) return;

    const menuItems = menu.querySelectorAll('li');
    menuItems.forEach(item => {
      item.addEventListener('click', () => {
        const action = item.getAttribute('data-action');

        switch (action) {
          case 'error-1':
            this.addAnnotation(1);
            break;
          case 'error-2':
            this.addAnnotation(2);
            break;
          case 'error-none':
            this.clearAnnotation();
            break;
        }

        menu.style.display = 'none';
      });
    });
  }

  /**
   * Add an annotation at the pending selection
   */
  addAnnotation(level) {
    if (!this.pendingSelection) {
      console.log('No selection to annotate');
      return;
    }

    const { start, end } = this.pendingSelection;

    // Remove any overlapping annotations
    this.annotations = this.annotations.filter(ann =>
      !(ann.start <= end && ann.end >= start)
    );

    // Add new annotation
    this.annotations.push({ start, end, level });

    // Sort by start position
    this.annotations.sort((a, b) => a.start - b.start);

    // Re-render
    this.render();

    // Clear selection
    window.getSelection().removeAllRanges();
    this.pendingSelection = null;

    // Notify change
    if (this.onChangeCallback) {
      this.onChangeCallback(this.annotations);
    }
  }

  /**
   * Clear annotation at the pending selection
   */
  clearAnnotation() {
    if (!this.pendingSelection) {
      console.log('No selection to clear');
      return;
    }

    const { start, end } = this.pendingSelection;

    // Remove annotations that overlap with selection
    const before = this.annotations.length;
    this.annotations = this.annotations.filter(ann =>
      !(ann.start <= end && ann.end >= start)
    );
    const after = this.annotations.length;

    console.log(`Cleared ${before - after} annotation(s)`);

    // Re-render
    this.render();

    // Clear selection
    window.getSelection().removeAllRanges();
    this.pendingSelection = null;

    // Notify change
    if (this.onChangeCallback) {
      this.onChangeCallback(this.annotations);
    }
  }

  /**
   * Render the text with highlighted annotations
   */
  render() {
    const container = document.getElementById(this.targetElementId);
    if (!container) return;

    // If no annotations, just show plain text
    if (this.annotations.length === 0) {
      container.innerHTML = this.escapeHtml(this.plainText);
      return;
    }

    // Sort annotations by start position
    const sorted = [...this.annotations].sort((a, b) => a.start - b.start);

    // Build HTML with highlights
    let html = '';
    let lastEnd = 0;

    for (const ann of sorted) {
      // Skip invalid annotations
      if (ann.start < lastEnd || ann.end >= this.plainText.length) {
        continue;
      }

      // Add text before this annotation
      if (ann.start > lastEnd) {
        html += this.escapeHtml(this.plainText.substring(lastEnd, ann.start));
      }

      // Add highlighted text
      const highlightClass = ann.level === 1 ? 'highlight-error-level-1' : 'highlight-error-level-2';
      const annotatedText = this.plainText.substring(ann.start, ann.end + 1);
      html += `<span class="${highlightClass}" data-start="${ann.start}" data-end="${ann.end}">${this.escapeHtml(annotatedText)}</span>`;

      lastEnd = ann.end + 1;
    }

    // Add remaining text
    if (lastEnd < this.plainText.length) {
      html += this.escapeHtml(this.plainText.substring(lastEnd));
    }

    container.innerHTML = html;
  }

  /**
   * Escape HTML special characters
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Get all annotations formatted for API submission
   */
  getAllAnnotations() {
    return this.annotations.map(ann => ({
      start: ann.start,
      end: ann.end,
      level: ann.level
    }));
  }

  /**
   * Set annotations (useful for loading from server)
   */
  setAnnotations(annotations) {
    this.annotations = annotations.map(ann => ({
      start: ann.start,
      end: ann.end,
      level: ann.level
    }));
    this.render();
  }

  /**
   * Set the plain text content
   */
  setText(text) {
    this.plainText = text;
    this.annotations = [];
    this.render();
  }

  /**
   * Get the plain text content
   */
  getText() {
    return this.plainText;
  }
}
