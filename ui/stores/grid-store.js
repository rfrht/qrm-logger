// Grid Store - handles all grid-related functionality
document.addEventListener('alpine:init', () => {
  Alpine.store('grid', {
    // Initialize from localStorage
    init() {
      // Always default showAll to false on page load
      this.showAll = false

      // Load persisted plot type (waterfall | average)
      try {
        const savedPlot = localStorage.getItem('grid_plot_type')
        if (savedPlot === 'waterfall' || savedPlot === 'average') {
          this.plotType = savedPlot
        }
      } catch (e) { /* ignore */ }

      // Load persisted image scale (10-100 in 10% steps)
      try {
        const saved = localStorage.getItem('grid_image_scale_percent')
        if (saved !== null && saved !== undefined) {
          const n = parseInt(saved, 10)
          if (Number.isFinite(n)) {
            const clamped = Math.max(10, Math.min(100, n))
            this.imageScalePercent = Math.round(clamped / 10) * 10
          }
        }
      } catch (e) { /* ignore */ }

      // Sync zoom modal with current URL at startup (supports deep-linking)
      try { this.applyZoomFromUrl() } catch (e) { /* ignore */ }

      // Listen for browser navigation (Back/Forward) to open/close zoom modal
      try {
        window.addEventListener('popstate', () => {
          try { this.applyZoomFromUrl() } catch (e) { /* ignore */ }
        })
      } catch (e) { /* ignore */ }
    },
    
    // State
    data: [],
    timeslices: {},
    gridTab: 'daily', // 'daily' | 'timeslices'
    showAll: false,
    imageScalePercent: 100,
    plotType: 'waterfall',
    
    // Zoom/Modal State
    showModal: false,
    zoomImageUrl: undefined,
    modalTitle: '',
    zoomLevel: 1,
    zoomLoading: false,
    panzoom: undefined,

    getVisibleData() {
        const id = Alpine.store('app').currentCaptureSetId
        const arr = this.data && this.data[id]
        return Array.isArray(arr) ? arr : []
    },

    getVisibleTimeSlices() {
        const id = Alpine.store('app').currentCaptureSetId
        const arr = this.timeslices && this.timeslices[id]
        return Array.isArray(arr) ? arr : []
    },

    // Group data by date with parts (windows)
    getGroupedData() {
        const items = this.getVisibleData()
        const map = {}
        for (const e of items) {
            const day = e.date
            if (!map[day]) map[day] = { date: day, parts: [] }
            map[day].parts.push(e)
        }
        const groups = Object.values(map)
        // Sort days newest first
        groups.sort((a, b) => (a.date < b.date ? 1 : (a.date > b.date ? -1 : 0)))
        // Sort parts by label (if present), otherwise keep as-is
        for (const g of groups) {
            const getStart = (label) => {
                if (!label || typeof label !== 'string') return -1
                const m = label.match(/^(\d{2})-/)
                return m ? parseInt(m[1], 10) : -1
            }
            g.parts.sort((p1, p2) => {
                const s1 = getStart(p1.label)
                const s2 = getStart(p2.label)
                // Latest window first (higher start hour first)
                return s2 - s1
            })
        }
        return groups
    },

    // Apply showAll toggle at the day level
    getVisibleGroupedData() {
        const groups = this.getGroupedData()
        return this.showAll ? groups : groups.slice(0, 1)
    },

    // Summary for current capture set: date range, number of days, and total images (parts)
    getSummary() {
        const items = this.getVisibleData()
        if (!items || items.length === 0) return null
        let minDate = items[0].date
        let maxDate = items[0].date
        const daySet = new Set()
        for (const e of items) {
            if (!e || !e.date) continue
            daySet.add(e.date)
            if (e.date < minDate) minDate = e.date
            if (e.date > maxDate) maxDate = e.date
        }
        return { start: minDate, end: maxDate, days: daySet.size, total: items.length }
    },

    // Actions
    async getData() {
      // Delegate to current tab (guard against disabled feature)
      if (this.gridTab === 'timeslices') {
        if (!this.isTimeSliceEnabled()) {
          this.gridTab = 'daily'
        } else {
          return this.getTimesliceData()
        }
      }
      const id = Alpine.store('app').currentCaptureSetId
      const pt = this.plotType || 'waterfall'
      const response = await fetch(`/grids?capture_set_id=${encodeURIComponent(id)}&plot_type=${encodeURIComponent(pt)}`)
      const json = await response.json()
      // API returns array for the capture set; store it under the current set id to keep existing accessors working
      this.data = { [id]: json.data }
    },

    async getTimesliceData() {
      const id = Alpine.store('app').currentCaptureSetId
      const pt = this.plotType || 'waterfall'
      const response = await fetch(`/timeslice_grids?capture_set_id=${encodeURIComponent(id)}&plot_type=${encodeURIComponent(pt)}`)
      const json = await response.json()
      this.timeslices = { [id]: (json && json.data) ? json.data : [] }
    },

    // Helper method to get the current grid image based on view mode
    getCurrentImage(grid, useResized = true, isFirst = false) {
      const imageUrl = useResized ? (grid.resized || grid.full) : (grid.full || grid.resized);
      if (!imageUrl) return null;
      // Add /output/ prefix to make the path work with the server's output route
      const fullUrl = '/output/' + imageUrl;
      return fullUrl;
    },

    getTimesliceImage(ts, useResized = true) {
      const imageUrl = useResized ? (ts.resized || ts.full) : (ts.full || ts.resized)
      if (!imageUrl) return null
      return '/output/' + imageUrl
    },


// Handle grid image click to open zoom modal
    openZoom(grid, isFirst) {
      const zoomImageUrl = this.getCurrentImage(grid, false, isFirst) || this.getCurrentImage(grid, true, isFirst);
      const captureSetId = (Alpine.store('app') && Alpine.store('app').currentCaptureSetId) || ''
      const titleParts = []
      if (captureSetId) titleParts.push(captureSetId)
      if (grid && grid.date) titleParts.push(grid.date)
      if (grid && grid.label) titleParts.push(`[${grid.label} h]`)
      const modalTitle = titleParts.join(' • ') || 'Grid View'
      // Push URL state so Back button closes the zoom view
      this.pushZoomState(zoomImageUrl, modalTitle)
      this.showZoomModal(zoomImageUrl, modalTitle);
    },

    showZoomModal(zoomImageUrl, modalTitle) {
      this.showModal = true;
      this.initZoom(zoomImageUrl, modalTitle);
    },

    initZoom(zoomImageUrl, modalTitle) {
      // If the same image is requested, keep current state (avoid reloading)
      if (this.zoomImageUrl === zoomImageUrl) {
        this.modalTitle = modalTitle || 'Grid View'
        return
      }

      // Begin loading state and attach listeners before updating the image source
      this.zoomLoading = true
      this.modalTitle = modalTitle || 'Grid View'
      this.zoomLevel = 1

      // Attach image load/error handlers to toggle loading indicator
      try {
        const img = document.getElementById('panzoom-element')
        if (img) {
          const onError = () => {
            this.zoomLoading = false
            try { img.removeEventListener('load', onLoad) } catch (e) {}
            try { img.removeEventListener('error', onError) } catch (e) {}
          }
          const onLoad = () => {
            this.zoomLoading = false
            try { img.removeEventListener('load', onLoad) } catch (e) {}
            try { img.removeEventListener('error', onError) } catch (e) {}
          }
          img.addEventListener('load', onLoad, { once: true })
          img.addEventListener('error', onError, { once: true })
        }
      } catch (e) { /* ignore */ }

      // Defer updating src so listeners are in place before the browser fires events
      setTimeout(() => { this.zoomImageUrl = zoomImageUrl }, 0)
      
      // Wait for DOM to be ready and initialize Panzoom
      setTimeout(() => {
        const elem = document.getElementById('panzoom-element')
        if (elem && window.Panzoom) {
          this.panzoom = Panzoom(elem, {
            maxScale: 30,
            minScale: 1,
            contain: false,
            panOnlyWhenZoomed: false
          })
          
          // Listen for zoom changes to update zoom level display
          elem.addEventListener('panzoomchange', (event) => {
            this.zoomLevel = Math.round(event.detail.scale * 100) / 100
          })
          
          // Panning and pinch zooming are bound automatically (unless disablePan is true).
          // There are several available methods for zooming
          // that can be bound on button clicks or mousewheel.
          elem.parentElement.addEventListener('wheel', this.panzoom.zoomWithWheel)
        }
      }, 100)
    },

    // Sync modal visibility with URL (?zoom=...) on navigation or initial load
    applyZoomFromUrl() {
      try {
        const url = new URL(window.location.href)
        const z = url.searchParams.get('zoom')
        const t = url.searchParams.get('title')
        if (z) {
          // If already showing the same image, do nothing
          if (this.showModal && this.zoomImageUrl === z) return
          this.showZoomModal(z, t || 'Grid View')
        } else {
          // No zoom param present -> ensure modal is closed (without touching history)
          if (this.showModal) {
            this.showModal = false
            if (this.panzoom) { try { this.panzoom.destroy() } catch (e) {} finally { this.panzoom = undefined } }
          }
        }
      } catch (e) { /* ignore */ }
    },

    // Push a history state reflecting the zoomed image so Back button closes it
    pushZoomState(zoomImageUrl, modalTitle) {
      try {
        const url = new URL(window.location.href)
        url.searchParams.set('zoom', zoomImageUrl)
        if (modalTitle) url.searchParams.set('title', modalTitle)
        history.pushState({ zoom: zoomImageUrl, title: modalTitle }, '', url)
      } catch (e) { /* ignore */ }
    },

    zoomIn() {
      if (this.panzoom) {
        this.panzoom.zoomIn()
      }
    },

    zoomOut() {
      if (this.panzoom) {
        this.panzoom.zoomOut()
      }
    },

    center() {
      if (this.panzoom) {
        // Center the image while preserving current zoom level
        this.panzoom.pan(0, 0)
      }
    },

    resetZoom() {
      if (!this.panzoom) return
      try { this.panzoom.reset() } catch (e) {
        // Fallbacks if reset() is unavailable
        try { this.panzoom.zoom(1, { animate: false }) } catch (e2) {
          try { this.panzoom.zoomTo(1, { animate: false }) } catch (e3) { /* ignore */ }
        }
        try { this.panzoom.pan(0, 0) } catch (e4) { /* ignore */ }
      }
      this.zoomLevel = 1
    },

    closeModal() {
      this.showModal = false;
      this.zoomLoading = false;
      if (this.panzoom) {
        this.panzoom.destroy();
        this.panzoom = undefined;
      }
      // Remove ?zoom from URL without adding a new history entry
      try {
        const url = new URL(window.location.href)
        if (url.searchParams.has('zoom')) {
          url.searchParams.delete('zoom')
          url.searchParams.delete('title')
          history.replaceState({}, '', url)
        }
      } catch (e) { /* ignore */ }
    },

    openZoomTimeslice(ts) {
      const zoomImageUrl = this.getTimesliceImage(ts, false) || this.getTimesliceImage(ts, true)
      const captureSetId = (Alpine.store('app') && Alpine.store('app').currentCaptureSetId) || ''
      const modalTitle = `${captureSetId} • Time-slice ${String(ts.hour).padStart(2,'0')}:00`
      this.pushZoomState(zoomImageUrl, modalTitle)
      this.showZoomModal(zoomImageUrl, modalTitle)
    },

    setGridTab(tab) {
      const wantTs = (tab === 'timeslices')
      const t = (wantTs && this.isTimeSliceEnabled()) ? 'timeslices' : 'daily'
      if (this.gridTab === t) return
      this.gridTab = t
      this.getData()
    },

    // Toggle showAll (non-persistent)
    toggleShowAll() {
      this.showAll = !this.showAll;
    },

    // Feature flag: Time-slices UI enabled when processing is enabled (regardless of configured hours)
    isTimeSliceEnabled() {
      try {
        const cfg = Alpine.store('config')?.values || {}
        return !!cfg.timeslice_autogenerate
      } catch (e) {
        return false
      }
    },

    // Global image scale controls (affect all images on the page)
    incImageScale() {
      const next = Math.min(100, (Math.round(this.imageScalePercent / 10) * 10) + 10)
      this.imageScalePercent = Math.max(10, Math.min(100, next))
      this.persistImageScale()
    },
    decImageScale() {
      const next = Math.max(10, (Math.round(this.imageScalePercent / 10) * 10) - 10)
      this.imageScalePercent = Math.max(10, Math.min(100, next))
      this.persistImageScale()
    },
    resetImageScale() {
      this.imageScalePercent = 100
      this.persistImageScale()
    },
    persistImageScale() {
      try { localStorage.setItem('grid_image_scale_percent', String(this.imageScalePercent)) } catch (e) { /* ignore */ }
    },

    // Format a YYYY-MM-DD date with weekday in English plus relative days, e.g., "2025-10-06 (Monday) - 3 days ago"
    formatDay(d) {
      try {
        let date;
        if (typeof d === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(d)) {
          const [y, m, dd] = d.split('-').map(n => parseInt(n, 10));
          date = new Date(y, m - 1, dd);
        } else {
          const tmp = new Date(d);
          if (isNaN(tmp.getTime())) return d;
          date = new Date(tmp.getFullYear(), tmp.getMonth(), tmp.getDate());
        }
        const weekday = date.toLocaleDateString('en-US', { weekday: 'long' });
        const now = (Alpine.store('app') && Alpine.store('app').now) ? Alpine.store('app').now : new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const diffDays = Math.floor((today - date) / (24 * 60 * 60 * 1000));
        if (diffDays <= 0) {
          return `${d} (${weekday})`;
        }
        const rel = diffDays === 1 ? '1 day ago' : `${diffDays} days ago`;
        return `${d} (${weekday}) - ${rel}`;
      } catch (e) {
        return `${d}`;
      }
    },

    // Toggle and persist plot type, then refresh data
    setPlotType(type) {
      const t = (type === 'average') ? 'average' : 'waterfall'
      if (this.plotType === t) return
      this.plotType = t
      try { localStorage.setItem('grid_plot_type', t) } catch (e) { /* ignore */ }
      this.getData()
    }
  })
})
