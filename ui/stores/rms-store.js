// RMS Data Store - handles all RMS-related functionality
document.addEventListener('alpine:init', () => {
  Alpine.store('rms', {
    // Initialize from localStorage
    init() {
      // Load persisted values from localStorage
      const savedDataType = localStorage.getItem('rms_dataType')
      const savedViewMode = localStorage.getItem('rms_viewMode')
      const savedThresholds = localStorage.getItem('rms_thresholds')
      
      if (savedDataType) this.dataType = savedDataType
      if (savedViewMode) this.viewMode = savedViewMode
      if (savedThresholds) {
        try {
          this.thresholds = JSON.parse(savedThresholds)
        } catch (e) {
          console.warn('Failed to parse saved RMS thresholds')
        }
      }
    },
    
    // State
    data: [],
    dataLoading: false,
    dataError: '',
    dataType: 'truncated', // 'standard' or 'truncated'  
    viewMode: 'raw', // 'raw' or 'delta'
    dataDelta: [], // Computed delta data
    columnHeaders: [], // Column headers in correct order

    // Visibility filter: show only most recent X entries by default
    showAll: false,
    entriesLimit: 300,
    
    // RMS Color Thresholds (will be persisted manually)
    thresholds: {
      medium: 20,     // Medium starts here - values below are "Low"
      high: 40,       // High starts here
      critical: 50    // Critical starts here
    },

    // Actions
    async getData() {
      try {
        this.dataLoading = true
        this.dataError = ''
        
        const id = Alpine.store('app').currentCaptureSetId
        const response = await fetch(`/rms_data?type=${this.dataType}&capture_set_id=${encodeURIComponent(id)}`)
        if (response.ok) {
          const data1 = await response.json()
          const rawData = data1.data
          
          // Clear the existing data first to force reactivity
          this.data = []
          this.dataDelta = []
          this.columnHeaders = []
          // Reset showAll flag to reapply the entries limit
          this.showAll = false
          // Use nextTick equivalent to ensure DOM update
          await new Promise(resolve => setTimeout(resolve, 10))
          
          // Handle new format: {headers: [], rows: []}
          if (rawData && rawData.headers && Array.isArray(rawData.rows)) {
            this.columnHeaders = rawData.headers
            // Convert rows to objects using headers
            this.data = rawData.rows.map(row => {
              const obj = {}
              rawData.headers.forEach((header, i) => {
                obj[header] = row[i] || ''
              })
              return obj
            })
          } else if (Array.isArray(rawData)) {
            // Fallback for old format (array of objects)
            this.data = rawData
            if (rawData.length > 0) {
              this.columnHeaders = Object.keys(rawData[0])
            }
          }
          
          // Calculate delta data
          this.calculateDelta()
          //console.log(`${this.dataType} RMS data loaded:`, this.data.length, 'records')
        } else {
          const errorData = await response.json()
          this.dataError = errorData.error || `Failed to load ${this.dataType} RMS data`
        }
      } catch (error) {
        console.error(`Error loading ${this.dataType} RMS data:`, error)
        this.dataError = `Error loading ${this.dataType} RMS data: ` + error.message
      } finally {
        this.dataLoading = false
      }
    },

    // Calculate delta values between consecutive rows
    calculateDelta() {
      if (!this.data || this.data.length < 2) {
        this.dataDelta = []
        return
      }
      
      const deltaData = []
      const keys = Object.keys(this.data[0])
      
      // Start from index 0 (latest) and compare with index i+1 (chronologically previous)
      for (let i = 0; i < this.data.length - 1; i++) {
        const currentRow = this.data[i]           // Latest time
        const previousRow = this.data[i + 1]     // Chronologically previous time
        const deltaRow = {}
        
        keys.forEach(key => {
          if (key === 'counter' || key === 'date' || key === 'time' || key === 'note') {
            // Keep immutable metadata from current row (latest time)
            deltaRow[key] = currentRow[key]
          } else {
            // Calculate delta: current - previous (positive = increase over time)
            const currentValue = parseFloat(currentRow[key])
            const previousValue = parseFloat(previousRow[key])
            
            if (!isNaN(currentValue) && !isNaN(previousValue)) {
              const delta = currentValue - previousValue
              deltaRow[key] = delta > 0 ? `+${delta.toFixed(0)}` : delta.toFixed(0)
            } else {
              deltaRow[key] = '0'
            }
          }
        })
        
        deltaData.push(deltaRow)
      }
      
      this.dataDelta = deltaData
    },

    // Get gradient color based on RMS value using configurable thresholds
    getColor(value) {
      const numValue = parseFloat(value)
      if (isNaN(numValue)) return 'transparent'
      
      const { medium, high, critical } = this.thresholds
      
      if (numValue < medium) {
        // Low interference - Grey
        return '#666666'
      } else if (numValue < high) {
        // Medium interference - Grey to darker yellow/amber gradient
        const ratio = (numValue - medium) / (high - medium)
        const r = Math.round(102 + (255 - 102) * ratio)  // 102 to 255 (red stays same)
        const g = Math.round(102 + (200 - 102) * ratio)  // 102 to 200 (less green, darker yellow)
        const b = Math.round(102 + (0 - 102) * ratio)    // 102 to 0 (blue to 0)
        return `rgb(${r}, ${g}, ${b})`
      } else if (numValue < critical) {
        // High interference - Darker yellow/amber to Red gradient
        const ratio = (numValue - high) / (critical - high)
        const r = 255  // Stay at 255
        const g = Math.round(200 + (0 - 200) * ratio)    // 200 to 0 (start from darker yellow)
        const b = 0    // Stay at 0
        return `rgb(${r}, ${g}, ${b})`
      } else {
        // Critical interference - Dark Red (above critical threshold)
        return '#CC0000'
      }
    },

    // Get color for delta values (different coloring for positive and negative)
    getDeltaColor(value) {
      const numValue = parseFloat(value)
      if (isNaN(numValue)) return 'transparent'
      
      if (numValue === 0) {
        return '#666666' // Grey for no change
      } else {
        const absValue = Math.abs(numValue)
        const { medium, high, critical } = this.thresholds
        
        // Scale delta thresholds relative to absolute thresholds (use smaller values)
        const deltaThresholds = {
          medium: medium * 0.3,  // 30% of medium threshold
          high: high * 0.3,      // 30% of high threshold 
          critical: critical * 0.3 // 30% of critical threshold
        }
        
        if (absValue < deltaThresholds.medium) {
          // Low delta - Grey
          return '#666666'
        } else if (numValue > 0) {
          // POSITIVE DELTAS - Use warm colors (yellow to red)
          if (absValue < deltaThresholds.high) {
            // Medium positive delta - Grey to darker yellow/amber gradient
            const ratio = (absValue - deltaThresholds.medium) / (deltaThresholds.high - deltaThresholds.medium)
            const r = Math.round(102 + (255 - 102) * ratio)  // 102 to 255
            const g = Math.round(102 + (200 - 102) * ratio)  // 102 to 200
            const b = Math.round(102 + (0 - 102) * ratio)    // 102 to 0
            return `rgb(${r}, ${g}, ${b})`
          } else if (absValue < deltaThresholds.critical) {
            // High positive delta - Darker yellow/amber to Red gradient
            const ratio = (absValue - deltaThresholds.high) / (deltaThresholds.critical - deltaThresholds.high)
            const r = 255  // Stay at 255
            const g = Math.round(200 + (0 - 200) * ratio)    // 200 to 0
            const b = 0    // Stay at 0
            return `rgb(${r}, ${g}, ${b})`
          } else {
            // Critical positive delta - Dark Red
            return '#CC0000'
          }
        } else {
          // NEGATIVE DELTAS - Use cool colors (blue to green)
          if (absValue < deltaThresholds.high) {
            // Medium negative delta - Grey to Blue gradient
            const ratio = (absValue - deltaThresholds.medium) / (deltaThresholds.high - deltaThresholds.medium)
            const r = Math.round(102 + (0 - 102) * ratio)    // 102 to 0
            const g = Math.round(102 + (100 - 102) * ratio)  // 102 to 100 (slight blue tint)
            const b = Math.round(102 + (255 - 102) * ratio)  // 102 to 255 (blue)
            return `rgb(${r}, ${g}, ${b})`
          } else if (absValue < deltaThresholds.critical) {
            // High negative delta - Blue to Green gradient
            const ratio = (absValue - deltaThresholds.high) / (deltaThresholds.critical - deltaThresholds.high)
            const r = Math.round(0 + (0 - 0) * ratio)        // Stay at 0
            const g = Math.round(100 + (200 - 100) * ratio)  // 100 to 200 (more green)
            const b = Math.round(255 + (0 - 255) * ratio)    // 255 to 0 (less blue)
            return `rgb(${r}, ${g}, ${b})`
          } else {
            // Critical negative delta - Dark Green
            return '#00AA00'
          }
        }
      }
    },

    // Get threshold range name for display
    getThresholdName(value) {
      const numValue = parseFloat(value)
      if (isNaN(numValue)) return 'Unknown'
      
      const { medium, high, critical } = this.thresholds
      
      if (numValue < medium) return 'Low'
      else if (numValue < high) return 'Medium'
      else if (numValue < critical) return 'High'
      else return 'Critical'
    },

    // Validate and update thresholds
    updateThresholds() {
      // Ensure thresholds are in ascending order
      const thresholds = [this.thresholds.medium, this.thresholds.high, this.thresholds.critical]
      const sorted = [...thresholds].sort((a, b) => a - b)
      
      if (JSON.stringify(thresholds) !== JSON.stringify(sorted)) {
        // Fix the order
        this.thresholds.medium = sorted[0]
        this.thresholds.high = sorted[1] 
        this.thresholds.critical = sorted[2]
      }
      
      // Save to localStorage
      this.saveThresholds()
    },

    // Check if a column should have RMS coloring (skip first four columns: counter, date, time, note)
    shouldColorCell(key) {
      if (!this.data || this.data.length === 0) return false
      // Use columnHeaders to get the correct visual order, not Object.keys which is arbitrary
      const keys = this.columnHeaders && this.columnHeaders.length > 0 
        ? this.columnHeaders 
        : Object.keys(this.data[0])
      const keyIndex = keys.indexOf(key)
      return keyIndex >= 4  // Color from fifth column onwards (after counter, date, time, note)
    },

    // Get the data to display based on view mode
    getCurrentData() {
      return this.viewMode === 'delta' ? this.dataDelta : this.data
    },

    // Get column keys in correct order from stored headers
    getColumnKeys() {
      // Use the explicitly stored column headers to preserve order
      if (this.columnHeaders && this.columnHeaders.length > 0) {
        return this.columnHeaders
      }
      // Fallback to extracting from data
      const data = this.getCurrentData()
      if (!Array.isArray(data) || data.length === 0) return []
      return Object.keys(data[0])
    },

    // Get the data visible in the table, honoring the entriesLimit unless showAll is true
    getVisibleData() {
      const source = this.getCurrentData()
      if (!Array.isArray(source) || source.length === 0) return []
      if (this.showAll) return source
      return source.slice(0, this.entriesLimit)
    },

    // Whether there are more rows beyond the entriesLimit
    hasMoreThanEntriesLimit() {
      const source = this.getCurrentData()
      if (!Array.isArray(source)) return false
      return source.length > this.entriesLimit
    },

    // Action to show all entries
    showAllEntries() {
      this.showAll = true
    },

    // Show date only for the latest entry of the day (data is newest-first)
    // Note: This method receives the full visibleData array from the template to avoid
    // repeatedly calling getVisibleData() which would slice the array on every row
    shouldShowDate(index, visibleData) {
      if (!Array.isArray(visibleData) || index < 0 || index >= visibleData.length) return false
      if (index === 0) return true
      const curr = visibleData[index]
      const prev = visibleData[index - 1]
      const currDate = this.extractDateString(curr && curr.date)
      const prevDate = this.extractDateString(prev && prev.date)
      return !!currDate && !!prevDate && currDate !== prevDate
    },

    // Date column now contains only 'YYYY-MM-DD'
    extractDateString(v) {
      if (typeof v !== 'string') return null
      return v
    },

    // Check if current view mode should use delta coloring
    shouldUseDeltaColoring() {
      return this.viewMode === 'delta'
    },

    // Change data type and reload
    async setDataType(type) {
      if (this.dataType !== type) {
          this.dataLoading = true
           // Clear the existing data first to force reactivity
          this.data = []
          this.dataDelta = []
          // Use nextTick equivalent to ensure DOM update
          await new Promise(resolve => setTimeout(resolve, 10))

        this.dataType = type
        localStorage.setItem('rms_dataType', type)
        await this.getData()
      }
    },

    // Change view mode and recalculate if needed
    setViewMode(mode) {
      if (this.viewMode !== mode) {
        this.viewMode = mode
        localStorage.setItem('rms_viewMode', mode)
        if (mode === 'delta' && this.data.length > 0) {
          this.calculateDelta()
        }
      }
    },
    
    // Save thresholds to localStorage
    saveThresholds() {
      localStorage.setItem('rms_thresholds', JSON.stringify(this.thresholds))
    }
  })
})
