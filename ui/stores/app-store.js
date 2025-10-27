// Application Store - handles status, recording, and scheduler functionality
document.addEventListener('alpine:init', () => {
  Alpine.store('app', {
    // State
    status: {},
    systemInfo: { free_disk_mb: null },
    statusError: '',
    statusPollIntervalSec: 2,
    statusPollTimerId: null,
    schedulerEnabled: false,
    sdrBusy: false,
    note: '',
    now: new Date(),
    lastRecordingState: false, // Track previous recording state
    currentCaptureSetId: null, // Will be set after loading capture sets
    captureSetIds: [], // Will be loaded from backend
    captureSetIdsLoaded: false, // Track if capture sets have been loaded and filtered
    viewMode: 'grid', // 'grid' | 'rms' | 'log'
    
    // Initialize the app store - called once when Alpine.js starts
    init() {
      // Load persisted viewMode from localStorage; default to 'grid' unless explicitly 'rms' or 'log'
      const savedViewMode = localStorage.getItem('grid_viewMode')
      this.viewMode = (savedViewMode === 'rms' || savedViewMode === 'log') ? savedViewMode : 'grid'
      
      // Load persisted capture set from localStorage
      const savedCaptureSet = localStorage.getItem('currentCaptureSetId')
      if (savedCaptureSet) {
        this.currentCaptureSetId = savedCaptureSet
      }

      // Load status polling interval (seconds) from localStorage; default to 2; 0 disables
      const savedInterval = localStorage.getItem('status_poll_interval_sec')
      if (savedInterval !== null && savedInterval !== '') {
        let n = parseInt(savedInterval, 10)
        if (!Number.isFinite(n)) n = 2
        if (n < 0) n = 0
        this.statusPollIntervalSec = n
      } else {
        this.statusPollIntervalSec = 2
      }
    },

    setCaptureSet(id) {
        this.currentCaptureSetId = id
        
        // Persist the selection to localStorage
        localStorage.setItem('currentCaptureSetId', id)
        
        // Close image selector when switching capture sets
        Alpine.store('image').close()
        
        // Reload data for the new capture set based on current view mode
        if (this.viewMode === 'rms') {
            Alpine.store('rms').getData()
        } else if (this.viewMode === 'grid') {
            Alpine.store('grid').getData()
        } else if (this.viewMode === 'log') {
            Alpine.store('log').getData()
        }
    },


    // Toast helper function
    showToast(message, type = 'info', title = '', zIndex = null) {
      const toastTitle = title || (type.charAt(0).toUpperCase() + type.slice(1))
      const colorMap = {
        success: 'green',
        error: 'red',
        warning: 'yellow',
        info: 'blue'
      }
      
      const options = {
        title: toastTitle,
        message: message,
        position: 'topRight',
        timeout: type === 'error' ? 6000 : 4000,
        theme: 'light',
        color: colorMap[type] || 'blue',
        progressBar: true,
        close: true,
        drag: true
      }
      
      // Add custom z-index if provided
      if (zIndex !== null) {
        options.zindex = zIndex
      }
      
      iziToast.show(options)
    },

    // Actions
    async refreshStatus() {
      try {
        const response = await fetch("/status")
        if (!response.ok) {
          throw new Error(`Status endpoint returned ${response.status}: ${response.statusText}`)
        }
        const json = await response.json()
        
        // Check if recording just finished to refresh data
        if (this.status.recording && !json.data.recording) {
          // Show recording completed toast
          this.showToast('', 'success', 'Recording Complete')
          
          // reload data after recording finished
          Alpine.store('grid').data = []
          Alpine.store('grid').getData()
          // Reload RMS/log data if in those views
          if (this.viewMode === 'rms') {
            Alpine.store('rms').getData()
          }
          if (this.viewMode === 'log') {
            Alpine.store('log').getData()
          }

          // Refresh system info (disk space) after a recording completes
          await this.refreshSystemInfo()
        }

        // Show start toast when recording starts (e.g., by scheduler)
        if (!this.status.recording && json.data.recording) {
          this.showToast('', 'info', 'Recording Start')
        }
        
        this.status = json.data
        this.statusError = '' // Clear any previous error

        // Sync scheduler UI state with backend status
        if (this.status.scheduler) {
          this.schedulerEnabled = this.status.scheduler.running
        }
      } catch (error) {
        console.error('Failed to refresh status:', error)
        this.statusError = `Status refresh failed: ${error.message}`
      }
    },

    async startRecord() {
      this.status.error_text = undefined
      let recordTime = parseInt(Alpine.store('config').values.rec_time_default_sec)
      if (isNaN(recordTime)) recordTime = 2
      
      // Show immediate toast when button is clicked
      this.showToast('', 'info', 'Recording Request')
      
      const payload = {
        method: 'POST',
        body: JSON.stringify({
          "sample_time": recordTime,
          "note": this.note
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      }
      
      try {
        this.status.recording = true
        const response = await fetch("/start", payload)
        const json = await response.json()
        
        if (response.ok) {
          this.status = json.data
        } else {
          this.showToast(json.error || 'Failed to start recording', 'error', 'Recording Error')
          this.status.recording = false
        }
      } catch (error) {
        this.showToast('Error starting recording: ' + error.message, 'error', 'Recording Error')
        this.status.recording = false
      }
    },

    async stopRecord() {
      try {
        const confirmed = window.confirm('Stop the current recording?')
        if (!confirmed) return
        this.showToast('', 'info', 'Recording Stop')
        const response = await fetch("/stop", { method: 'POST' })
        if (!response.ok) {
          const json = await response.json().catch(() => ({}))
          this.showToast(json.error || 'Failed to stop recording', 'error', 'Recording Error')
        }
        await this.refreshStatus()
      } catch (error) {
        this.showToast('Error stopping recording: ' + error.message, 'error', 'Recording Error')
      }
    },


    async toggleScheduler() {
      try {
        const action = this.schedulerEnabled ? 'stop' : 'start'
        const payload = {
          method: 'POST',
          body: JSON.stringify({
            action: action
          }),
          headers: {
            'Content-Type': 'application/json'
          }
        }
        
        const response = await fetch("/scheduler", payload)
        const json = await response.json()
        
        if (response.ok) {
          // Update scheduler status immediately from server response
          if (json.data.scheduler) {
            this.schedulerEnabled = json.data.scheduler.running
            // Also update the status object so the label updates immediately
            if (!this.status.scheduler) {
              this.status.scheduler = {}
            }
            this.status.scheduler.running = json.data.scheduler.running
            
            // Show success toast
            const actionText = json.data.scheduler.running ? 'started' : 'stopped'
            this.showToast(`Scheduler ${actionText} successfully`, 'success', 'Scheduler')
          }
          
          // Refresh full status to ensure everything is up to date
          this.refreshStatus()
        } else {
          console.error('Scheduler', action, 'failed:', json)
          // Revert the switch state on error
          this.schedulerEnabled = !this.schedulerEnabled
        }
      } catch (error) {
        console.error('Error toggling scheduler:', error)
        // Revert the switch state on error
        this.schedulerEnabled = !this.schedulerEnabled
      }
    },

    async setSdrActive(active) {
      if (this.sdrBusy) return
      this.sdrBusy = true
      if (!!active) {
          this.showToast(`SDR starting`, 'success', 'SDR')
      }

      try {
        const response = await fetch('/sdr-control', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 'sdr-active': !!active })
        })
        const json = await response.json().catch(() => ({}))
        if (response.ok) {
          const activeNow = !!(json?.data?.sdr_active)
          if (!this.status) this.status = {}
          this.status.sdr_active = activeNow
          const actionText = activeNow ? 'started' : 'stopped'
          this.showToast(`SDR ${actionText}`, 'success', 'SDR')
        } else {
          this.showToast(json.error || 'Failed to set SDR state', 'error', 'SDR Error')
        }
      } catch (error) {
        this.showToast('Error setting SDR state: ' + error.message, 'error', 'SDR Error')
      } finally {
        this.sdrBusy = false
      }
    },

    timeDelta(nextTime) {
      const next = new Date(nextTime);
      if (!isNaN(next)) {
        const totalSeconds = Math.floor((next - this.now) / 1000); // Convert ms to seconds
        if (totalSeconds <= 0) {
          return '0 min 0 sec';
        }
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes} min ${seconds} sec`;
      }
      return 'Invalid date';
    },

    formatTimeOnly(dateTimeString) {
      if (!dateTimeString) return '';
      // Extract time from 'YYYY-MM-DD HH:MM:SS' format
      const parts = dateTimeString.split(' ');
      if (parts.length >= 2) {
        const timeParts = parts[1].split(':');
        if (timeParts.length >= 2) {
          return `${timeParts[0]}:${timeParts[1]}`; // Return HH:MM format
        }
        return parts[1]; // Return as-is if time format is unexpected
      }
      return dateTimeString; // Return as-is if format is unexpected
    },

    formatDateOnly(dateTimeString) {
      if (!dateTimeString) return '';
      const parts = dateTimeString.split(' ');
      if (parts.length >= 1) {
        return parts[0]; // YYYY-MM-DD
      }
      return '';
    },

    isSameDay(dateTimeString) {
      if (!dateTimeString) return true;
      const parts = dateTimeString.split(' ');
      if (parts.length >= 1) {
        const nextDateStr = parts[0]; // YYYY-MM-DD
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const todayStr = `${yyyy}-${mm}-${dd}`;
        return nextDateStr === todayStr;
      }
      return true;
    },

    setViewMode(mode) {
      this.viewMode = mode;
      localStorage.setItem('grid_viewMode', mode);
      // Load data when switching views
      if (mode === 'grid') {
        Alpine.store('grid').getData();
      } else if (mode === 'rms') {
        Alpine.store('rms').getData();
      } else if (mode === 'log') {
        Alpine.store('log').getData();
      }
    },

    async refreshCaptureSetIds() {
      try {
        // Load capture sets and config to filter enabled sets for the UI button list
        const setsResp = await fetch('/capture_sets')
        const setsJson = setsResp.ok ? await setsResp.json() : { data: [] }
        const allSetIds = Array.isArray(setsJson.data) ? setsJson.data : []

        await Alpine.store('config').loadValues()
        const enabledIds = (Alpine.store('config').values.capture_sets_enabled || [])
        const enabledSet = new Set(enabledIds)

        // Always include ROI sets (ids ending with _ROI). Filter base sets by enabled list.
        const roiIds = allSetIds.filter(id => typeof id === 'string' && id.endsWith('_ROI'))
        const baseIds = allSetIds.filter(id => typeof id === 'string' && !id.endsWith('_ROI'))
        const filteredBase = baseIds.filter(id => enabledSet.has(id))
        const merged = [...filteredBase, ...roiIds]
        this.captureSetIds = merged.length ? merged : allSetIds

        // Check localStorage first, then validate against available sets
        const savedCaptureSet = localStorage.getItem('currentCaptureSetId')
        if (savedCaptureSet && this.captureSetIds.includes(savedCaptureSet)) {
          this.currentCaptureSetId = savedCaptureSet
        } else if (!this.currentCaptureSetId || !this.captureSetIds.includes(this.currentCaptureSetId)) {
          // Fallback to first available set if no valid saved selection
          this.currentCaptureSetId = this.captureSetIds[0] || null
          // Update localStorage with the fallback selection
          if (this.currentCaptureSetId) {
            localStorage.setItem('currentCaptureSetId', this.currentCaptureSetId)
          }
        }
        
        // Mark as loaded
        this.captureSetIdsLoaded = true
      } catch (e) {
        console.error('Error refreshing capture sets:', e)
        if (!Array.isArray(this.captureSetIds)) this.captureSetIds = []
        this.captureSetIdsLoaded = true // Still mark as loaded to prevent infinite loading
      }
    },

    async startRefreshInterval() {
      try {
        // Use the new method to refresh capture sets
        await this.refreshCaptureSetIds()
        await this.refreshStatus()
        await this.refreshSystemInfo()

        // Load data for the current view mode
        if (this.viewMode === 'grid') {
          Alpine.store('grid').getData()
        } else if (this.viewMode === 'rms') {
          Alpine.store('rms').getData()
        } else if (this.viewMode === 'log') {
          Alpine.store('log').getData()
        }
      } catch (e) {
        console.error('Error initializing capture sets/config:', e)
        if (!Array.isArray(this.captureSetIds)) this.captureSetIds = []
      }

      // Apply status polling based on configured interval (seconds)
      this.applyStatusPolling()
      
      // Independent timer for live countdown updates
      setInterval(() => {
        this.now = new Date()
      }, 2000)
    },

    // Load system info
    async refreshSystemInfo() {
      try {
        const res = await fetch('/system-info')
        if (!res.ok) return
        const json = await res.json()
        this.systemInfo = json.data || { free_disk_mb: null }
      } catch (e) {
        console.warn('Failed to load system info:', e)
      }
    },

    // Update or stop the periodic status refresh based on interval setting
    applyStatusPolling() {
      if (this.statusPollTimerId) {
        clearInterval(this.statusPollTimerId)
        this.statusPollTimerId = null
      }
      const sec = this.statusPollIntervalSec
      if (typeof sec === 'number' && sec > 0) {
        this.statusPollTimerId = setInterval(() => {
          this.refreshStatus()
        }, sec * 1000)
      }
    },

    // Setter from UI text field; persist to localStorage; accepts 0 to disable; blanks reset to default (2)
    setStatusPollInterval(value) {
      const v = (value ?? '').toString().trim()
      let n
      if (v === '') {
        n = 2 // reset to default when cleared
      } else {
        n = parseInt(v, 10)
        if (!Number.isFinite(n)) n = 2
        if (n < 0) n = 0
      }
      this.statusPollIntervalSec = n
      localStorage.setItem('status_poll_interval_sec', String(n))
      this.applyStatusPolling()
    },

    // Formatting helpers
    formatMB(mb) {
      if (mb === null || mb === undefined) return 'N/A'
      if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB'
      return mb + ' MB'
    },
    diskSpaceStyle() {
      const mb = this.systemInfo?.free_disk_mb
      let color = '#dbdbdb'
      if (typeof mb === 'number') {
        if (mb < 500) color = 'red'
        else if (mb < 2048) color = '#ffdd57'
      }
      return `color: ${color}; font-weight: normal; margin-left: 0.25rem;`
    },
    diskSpaceWarning() {
      const mb = this.systemInfo?.free_disk_mb
      if (typeof mb !== 'number') return ''
      if (mb < 500) return '(INSUFFICIENT SPACE)'
      if (mb < 2048) return '(LOW SPACE)'
      return ''
    }
  })
})
