// Configuration Store - handles all configuration-related functionality
document.addEventListener('alpine:init', () => {
  Alpine.store('config', {
    // State
    showModal: false,
    activeTab: 'general',
    form: {
      rf_gain: 0,
      if_gain: -35,
      sdr_bandwidth: 0,
      sdr_shutdown_after_recording: true,
      rec_time_default_sec: 0,
      scheduler_cron: '*/15 * * * *',
      scheduler_autostart: false,
      fft_size: 0,
      min_db: 0,
      max_db: 0,
      capture_sets_enabled:[],
      capture_set_configurations: {}
    },
    // ROI editor state (working copy, not saved until Save pressed)
    roisProcessingEnabled: false,
    roisWorking: [],
    roiEditMode: 'none', // 'none' | 'add' | 'edit'
    roiSelectedIndex: null,
    roiForm: {
      roi_id: '',
      base_capture_set_id: '',
      capture_spec_id: '',
      center_khz: '',
      span_khz: '',
      margin_khz: '' // optional
    },
    values: {
      rf_gain: 0,
      if_gain: -35,
      sdr_bandwidth: 0,
      sdr_shutdown_after_recording: true,
      rec_time_default_sec: 0,
      scheduler_cron: '*/15 * * * *',
      scheduler_autostart: false,
      fft_size: 0,
      min_db: 0,
      max_db: 0,
      capture_sets_enabled:[],
      capture_set_configurations: {}
    },
    sdrOptions: null, // Will be loaded from /sdr-options endpoint
    error: '',
    success: '',
    saving: false,
    availableCaptureSets: [], // Will be loaded from /capture_sets endpoint
    captureSetsWithSpecs: {}, // Map of capture_set_id -> [spec objects with full details]
    availableCaptureSpecs: [], // Specs for currently selected capture set in ROI form
    selectedCaptureSpec: null, // Currently selected spec object with freq_range
    
    // Capture set info overlay state
    showCaptureSetInfo: false,
    captureSetInfoId: null,

    // UI-only state (not persisted to backend)
    ui: {
      spectrumDbEditMode: (typeof localStorage !== 'undefined' && localStorage.getItem('spectrum_db_edit_mode') === 'minmax') ? 'minmax' : 'noisefloor',
      spectrum_noise_floor_db: 0,
      spectrum_dynamic_range_db: 0,
    },

    // Helpers
    cronToText(expr) {
      try {
        if (!window.cronstrue || !expr || typeof expr !== 'string') return ''
        return window.cronstrue.toString(expr.trim(), { use24HourTimeFormat: true })
      } catch (e) {
        return 'Invalid cron expression'
      }
    },

    // Actions
    async loadValues() {
      try {
        const response = await fetch('/config')
        if (response.ok) {
          const data = await response.json()
          this.values = data.data
        } else {
          console.error('Failed to load config values for display')
        }
      } catch (error) {
        console.error('Error loading config values:', error)
      }
    },

    async loadSdrOptions() {
      try {
        const response = await fetch('/sdr-options')
        if (response.ok) {
          const data = await response.json()
          this.sdrOptions = data.data
        } else {
          console.error('Failed to load SDR options')
        }
      } catch (error) {
        console.error('Error loading SDR options:', error)
      }
    },

    async loadAvailableCaptureSets() {
      try {
        const response = await fetch('/capture_sets')
        if (response.ok) {
          const data = await response.json()
          const list = Array.isArray(data.data) ? data.data : []
          // For config UI (general and ROI editor), only show base sets (exclude *_ROI)
          this.availableCaptureSets = list.filter(id => typeof id === 'string' && !id.endsWith('_ROI'))
        } else {
          console.error('Failed to load available capture sets')
        }
      } catch (error) {
        console.error('Error loading available capture sets:', error)
      }
    },

    async loadCaptureSetsWithSpecs() {
      try {
        const response = await fetch('/capture_sets_with_specs')
        if (response.ok) {
          const data = await response.json()
          this.captureSetsWithSpecs = data.data || {}
        } else {
          console.error('Failed to load capture sets with specs')
        }
      } catch (error) {
        console.error('Error loading capture sets with specs:', error)
      }
    },

    updateAvailableCaptureSpecs(captureSetId, preserveSpecId = false) {
      // Update available specs when capture set changes
      if (captureSetId && this.captureSetsWithSpecs[captureSetId]) {
        this.availableCaptureSpecs = this.captureSetsWithSpecs[captureSetId]
      } else {
        this.availableCaptureSpecs = []
      }
      // Reset selected spec and clear capture_spec_id (unless preserving for edit)
      if (!preserveSpecId) {
        this.selectedCaptureSpec = null
        this.roiForm.capture_spec_id = ''
      }
    },

    updateSelectedCaptureSpec(specId) {
      // Update selected spec details when spec ID changes
      if (!specId || !this.availableCaptureSpecs) {
        this.selectedCaptureSpec = null
        return
      }
      const spec = this.availableCaptureSpecs.find(s => s.id === specId)
      this.selectedCaptureSpec = spec || null
    },

    getSpecFreqRangeText() {
      // Get frequency range text for display
      if (!this.selectedCaptureSpec) return ''
      if (this.selectedCaptureSpec.freq_range) {
        const start = this.selectedCaptureSpec.freq_range.freq_start
        const end = this.selectedCaptureSpec.freq_range.freq_end
        return `${start} - ${end} kHz`
      }
      // No freq_range, use freq ± span/2 if span exists, otherwise use freq ± bandwidth/2
      const freq = this.selectedCaptureSpec.freq
      if (this.selectedCaptureSpec.span) {
        const halfSpan = this.selectedCaptureSpec.span / 2
        return `${freq - halfSpan} - ${freq + halfSpan} kHz (approx)`
      }
      // Use SDR bandwidth as fallback
      const bandwidth = this.form.sdr_bandwidth || 2048
      const halfBw = bandwidth / 2
      return `${freq - halfBw} - ${freq + halfBw} kHz (SDR BW)`
    },

    async openModal() {
      try {
        // Clear previous messages
        this.error = ''
        this.success = ''
        this.activeTab = this.activeTab || 'general'
        
        // Load SDR options and available capture sets
        await this.loadSdrOptions()
        await this.loadAvailableCaptureSets()
        await this.loadCaptureSetsWithSpecs()
        
        // Load current configuration from server
        const response = await fetch('/config')
        if (response.ok) {
          const data = await response.json()
          this.form = { ...data.data }
          // Ensure configurations mapping exists for UI binding
          if (!this.form.capture_set_configurations || typeof this.form.capture_set_configurations !== 'object') {
            this.form.capture_set_configurations = {}
          }
          // Create empty config entries for each available set so nested x-model bindings are safe
          for (const id of this.availableCaptureSets) {
            if (!this.form.capture_set_configurations[id] || typeof this.form.capture_set_configurations[id] !== 'object') {
              this.form.capture_set_configurations[id] = {}
            }
          }
          // Initialize UI dB editing fields based on loaded min/max
          this.syncUiFromForm()
          // Load preferred edit mode from localStorage
          try {
            const savedMode = localStorage.getItem('spectrum_db_edit_mode')
            this.ui.spectrumDbEditMode = (savedMode === 'minmax') ? 'minmax' : 'noisefloor'
          } catch (e) {
            this.ui.spectrumDbEditMode = 'noisefloor'
          }
        } else {
          this.error = 'Failed to load current configuration'
        }
        
        // Load current ROI configuration (working copy)
        try {
          const r = await fetch('/rois')
          if (r.ok) {
            const j = await r.json()
            const cfg = j.data || {}
            this.roisProcessingEnabled = !!cfg.processing_enabled
            this.roisWorking = Array.isArray(cfg.rois) ? JSON.parse(JSON.stringify(cfg.rois)) : []
          } else {
            this.roisProcessingEnabled = false
            this.roisWorking = []
          }
        } catch (e) {
          console.warn('Failed to load ROIs', e)
          this.roisProcessingEnabled = false
          this.roisWorking = []
        }
        
        // Reset ROI editor state
        this.roiEditMode = 'none'
        this.roiSelectedIndex = null
        this.roiForm = { roi_id:'', base_capture_set_id:'', capture_spec_id:'', center_khz:'', span_khz:'', margin_khz:'' }
        
        this.showModal = true
      } catch (error) {
        console.error('Error loading configuration:', error)
        this.error = 'Error loading configuration: ' + error.message
        this.showModal = true
      }
    },

    async saveConfiguration() {
      try {
        this.saving = true
        this.error = ''
        this.success = ''
        
        // Ensure underlying min/max reflect current UI mode before validating
        if (this.ui.spectrumDbEditMode === 'noisefloor') {
          this.syncFormFromUi()
        }
        
        // Validate form data
        // Build per-capture-set configurations with bandwidth only when explicitly selected
        const rawCfgs = (this.form.capture_set_configurations && typeof this.form.capture_set_configurations === 'object') ? this.form.capture_set_configurations : {}
        const cfgs = {}
        for (const id of this.availableCaptureSets) {
          const entry = rawCfgs[id]
          const bw = entry ? entry.bandwidth : undefined
          if (bw !== '' && bw !== null && bw !== undefined) {
            cfgs[id] = { bandwidth: Number(bw) }
          }
        }

        const config = {
          rf_gain: parseInt(this.form.rf_gain),
          if_gain: parseInt(this.form.if_gain),
          sdr_bandwidth: parseInt(this.form.sdr_bandwidth),
          rec_time_default_sec: parseInt(this.form.rec_time_default_sec),
          scheduler_cron: (typeof this.form.scheduler_cron === 'string' ? this.form.scheduler_cron.trim() : ''),
          scheduler_autostart: !!this.form.scheduler_autostart,
          fft_size: parseInt(this.form.fft_size),
          min_db: parseInt(this.form.min_db),
          max_db: parseInt(this.form.max_db),
          capture_sets_enabled: this.form.capture_sets_enabled,
          sdr_shutdown_after_recording: !!this.form.sdr_shutdown_after_recording,
          capture_set_configurations: cfgs,
        }
        
        // Check for invalid values (except dB values and RF gain which can be negative)
        const positiveFields = ['sdr_bandwidth', 'rec_time_default_sec', 'fft_size']
        if (positiveFields.some(field => isNaN(config[field]) || config[field] <= 0)) {
          this.error = 'Bandwidth, time, and FFT size must be positive numbers'
          return
        }
        
        // Validate cron expression
        if (!config.scheduler_cron) {
          this.error = 'Cron expression is required'
          return
        }
        // Basic 5-field cron shape validation (not exhaustive)
        const cronParts = config.scheduler_cron.trim().split(/\s+/)
        if (cronParts.length !== 5) {
          this.error = 'Cron expression must have 5 space-separated fields (min hour dom mon dow)'
          return
        }
        
        // Check RF gain separately (can be any number but must be valid)
        if (isNaN(config.rf_gain)) {
          this.error = 'RF gain must be a valid number'
          return
        }
        
        // Check dB values
        if (isNaN(config.min_db) || isNaN(config.max_db)) {
          this.error = 'dB values must be valid numbers'
          return
        }
        
        if (config.min_db >= config.max_db) {
          this.error = 'Minimum dB must be less than maximum dB'
          return
        }
        
        // Send update to server
        const response = await fetch('/config', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(config)
        })
        
        const data = await response.json()
        
        if (response.ok) {
          // After config saved, save ROI configuration
          const roiPayload = { processing_enabled: !!this.roisProcessingEnabled, rois: this.roisWorking.map(r => {
            // Build minimal object with required fields; include margin if provided
            const m = {}
            m.roi_id = (r.roi_id || '').trim()
            m.base_capture_set_id = (r.base_capture_set_id || '').trim()
            m.capture_spec_id = (r.capture_spec_id || '').trim()
            m.center_khz = (r.center_khz === '' || r.center_khz === null || r.center_khz === undefined) ? '' : Number(r.center_khz)
            m.span_khz = (r.span_khz === '' || r.span_khz === null || r.span_khz === undefined) ? '' : Number(r.span_khz)
            if (r.margin_khz !== '' && r.margin_khz !== null && r.margin_khz !== undefined) {
              m.margin_khz = Number(r.margin_khz)
            }
            return m
          }) }

          // Validate ROI entries client-side (presence and numeric types)
          for (const rr of roiPayload.rois) {
            if (!rr.roi_id || !rr.base_capture_set_id || !rr.capture_spec_id || rr.center_khz === '' || rr.span_khz === '') {
              this.error = 'ROI entries must have roi_id, base_capture_set_id, capture_spec_id, center_khz, span_khz'
              this.saving = false
              return
            }
            if (isNaN(rr.center_khz) || isNaN(rr.span_khz)) {
              this.error = 'ROI numeric fields must be valid numbers'
              this.saving = false
              return
            }
          }

          const roiRes = await fetch('/rois', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(roiPayload)
          })
          const roiJson = await roiRes.json().catch(() => ({}))

          if (!roiRes.ok) {
            Alpine.store('app').showToast(roiJson.error || 'Failed to save ROIs', 'error', 'ROI Error')
            this.saving = false
            return
          }

          Alpine.store('app').showToast('Configuration saved successfully!', 'success', 'Saved')
          
          // Update displayed config values
          this.values = data.data.current_config
          
          // Refresh capture set buttons and display to reflect changes
          await Alpine.store('app').refreshCaptureSetIds()
          
          // Close modal after a short delay
          setTimeout(() => {
            this.showModal = false
          }, 500)
        } else {
          Alpine.store('app').showToast(data.error || 'Failed to update configuration', 'error', 'Configuration Error')
        }
        
      } catch (error) {
        console.error('Error saving configuration:', error)
        this.error = 'Error saving configuration: ' + error.message
      } finally {
        this.saving = false
      }
    },

    async startCalibration() {
      try {
        this.error = ''
        this.success = ''
        
        // Check if recording is already in progress
        if (Alpine.store('app').status.recording) {
          Alpine.store('app').showToast('Recording is already in progress. Please wait for it to complete.', 'warning', 'Calibration Error')
          return
        }
        
        // Get the current recording time from config
        let recordTime = parseInt(this.form.rec_time_default_sec)
        if (isNaN(recordTime)) recordTime = 5
        
        // Show immediate feedback and close modal right away
        Alpine.store('app').showToast(`Starting calibration recording...`, 'info', 'Calibration Request')
        this.showModal = false
        
        // Immediately update the app status to show recording is starting
        Alpine.store('app').status.recording = true
        
        const payload = {
          method: 'POST',
          body: JSON.stringify({
            "sample_time": recordTime,
            "note": "calib",
            "calibration": true
          }),
          headers: {
            'Content-Type': 'application/json'
          }
        }
        
        const response = await fetch("/start", payload)
        const json = await response.json()
        
        if (response.ok) {
          Alpine.store('app').showToast('Calibration recording started!', 'success', 'Calibration Started')
          // Update app status with server response
          Alpine.store('app').status = json.data
        } else {
          Alpine.store('app').showToast(json.msg || 'Failed to start calibration recording', 'error', 'Calibration Error')
          // Revert recording state on error
          Alpine.store('app').status.recording = false
        }
        
      } catch (error) {
        console.error('Error starting calibration:', error)
        Alpine.store('app').showToast('Error starting calibration: ' + error.message, 'error', 'Calibration Error')
      }
    },

    closeModal() {
      this.showModal = false
      this.error = ''
      this.success = ''
    },

    setActiveTab(tab) {
      this.activeTab = tab
    },

    // ROI editor methods
    startAddRoi() {
      this.roiEditMode = 'add'
      this.roiSelectedIndex = null
      this.roiForm = { roi_id:'', base_capture_set_id:'', capture_spec_id:'', center_khz:'', span_khz:'', margin_khz:'' }
      this.availableCaptureSpecs = []
      this.selectedCaptureSpec = null
      // Switch to ROI tab if not already
      this.activeTab = 'roi'
    },

    selectRoi(index) {
      if (index < 0 || index >= this.roisWorking.length) return
      this.roiSelectedIndex = index
      const r = this.roisWorking[index]
      
      // Update available specs FIRST before setting the form (preserve spec ID for edit)
      this.updateAvailableCaptureSpecs(r.base_capture_set_id, true)
      
      // Now set the form with all values
      this.roiForm = {
        roi_id: r.roi_id || '',
        base_capture_set_id: r.base_capture_set_id || '',
        capture_spec_id: r.capture_spec_id || '',
        center_khz: r.center_khz ?? '',
        span_khz: r.span_khz ?? '',
        margin_khz: (r.margin_khz !== undefined ? r.margin_khz : '')
      }
      
      // Update selected spec details for freq range display
      this.updateSelectedCaptureSpec(r.capture_spec_id)
      
      this.roiEditMode = 'edit'
      this.activeTab = 'roi'
    },

    applyRoiForm() {
      // Validate
      const f = this.roiForm
      if (!f.roi_id || !f.base_capture_set_id || !f.capture_spec_id || f.center_khz === '' || f.span_khz === '') {
        this.error = 'Please fill ROI ID, capture set, capture spec, center and span.'
        return
      }
      const center = Number(f.center_khz)
      const span = Number(f.span_khz)
      if (isNaN(center) || isNaN(span)) {
        this.error = 'Center and span must be valid numbers'
        return
      }
      
      // Validate that center frequency is within the selected spec's frequency range
      if (this.selectedCaptureSpec && this.selectedCaptureSpec.freq_range) {
        const freqRange = this.selectedCaptureSpec.freq_range
        const rangeStart = freqRange.freq_start
        const rangeEnd = freqRange.freq_end
        
        if (center < rangeStart || center > rangeEnd) {
          this.error = `Center frequency ${center} kHz is outside the valid range: ${rangeStart} - ${rangeEnd} kHz`
          return
        }
      }
      const entry = {
        roi_id: f.roi_id.trim(),
        base_capture_set_id: f.base_capture_set_id.trim(),
        capture_spec_id: f.capture_spec_id.trim(),
        center_khz: center,
        span_khz: span
      }
      if (f.margin_khz !== '' && f.margin_khz !== null && f.margin_khz !== undefined) {
        const m = Number(f.margin_khz)
        if (!isNaN(m)) entry.margin_khz = m
      }

      if (this.roiEditMode === 'add') {
        this.roisWorking.push(entry)
      } else if (this.roiEditMode === 'edit' && this.roiSelectedIndex !== null) {
        this.roisWorking.splice(this.roiSelectedIndex, 1, entry)
      }

      // Clear error message on success
      this.error = ''
      
      // Reset editor
      this.roiEditMode = 'none'
      this.roiSelectedIndex = null
      this.roiForm = { roi_id:'', base_capture_set_id:'', capture_spec_id:'', center_khz:'', span_khz:'', margin_khz:'' }
    },

    deleteSelectedRoi() {
      if (this.roiEditMode !== 'edit' || this.roiSelectedIndex === null) return
      if (!confirm('Delete selected ROI?')) return
      this.roisWorking.splice(this.roiSelectedIndex, 1)
      this.roiEditMode = 'none'
      this.roiSelectedIndex = null
      this.roiForm = { roi_id:'', base_capture_set_id:'', capture_spec_id:'', center_khz:'', span_khz:'', margin_khz:'' }
    },

    cancelRoiEdit() {
      this.roiEditMode = 'none'
      this.roiSelectedIndex = null
      this.roiForm = { roi_id:'', base_capture_set_id:'', capture_spec_id:'', center_khz:'', span_khz:'', margin_khz:'' }
    },

    getRoiFrequencyRanges() {
      // Calculate frequency ranges with and without margin for display
      const center = Number(this.roiForm.center_khz)
      const span = Number(this.roiForm.span_khz)
      const margin = Number(this.roiForm.margin_khz) || 0
      
      if (isNaN(center) || isNaN(span) || span <= 0) {
        return null
      }
      
      const coreStart = center - (span / 2)
      const coreEnd = center + (span / 2)
      const withMarginStart = coreStart - margin
      const withMarginEnd = coreEnd + margin
      
      return {
        core: `${coreStart.toFixed(1)} - ${coreEnd.toFixed(1)} kHz`,
        withMargin: margin > 0 ? `${withMarginStart.toFixed(1)} - ${withMarginEnd.toFixed(1)} kHz` : null
      }
    },

    // Spectrum UI helpers
    setDbEditMode(mode) {
      const m = (mode === 'noisefloor') ? 'noisefloor' : 'minmax'
      this.ui.spectrumDbEditMode = m
      try { localStorage.setItem('spectrum_db_edit_mode', m) } catch (e) {}
      // When switching to noise floor mode, make sure UI fields mirror current min/max
      if (m === 'noisefloor') {
        this.syncUiFromForm()
      }
    },

    syncUiFromForm() {
      const min = Number(this.form.min_db)
      const max = Number(this.form.max_db)
      if (Number.isFinite(min) && Number.isFinite(max)) {
        this.ui.spectrum_noise_floor_db = min
        const dr = max - min
        this.ui.spectrum_dynamic_range_db = Number.isFinite(dr) ? Math.max(0, dr) : 0
      }
    },

    syncFormFromUi() {
      const nf = Number(this.ui.spectrum_noise_floor_db)
      const dr = Number(this.ui.spectrum_dynamic_range_db)
      if (Number.isFinite(nf) && Number.isFinite(dr)) {
        this.form.min_db = nf
        this.form.max_db = nf + dr
      }
    },

    // Capture set info overlay methods
    openCaptureSetInfo(captureSetId) {
      this.captureSetInfoId = captureSetId
      this.showCaptureSetInfo = true
    },

    closeCaptureSetInfo() {
      this.showCaptureSetInfo = false
      this.captureSetInfoId = null
    },

    getCaptureSetInfoData() {
      // Return structured data for table display
      if (!this.captureSetInfoId || !this.captureSetsWithSpecs[this.captureSetInfoId]) {
        return null
      }
      
      const specs = this.captureSetsWithSpecs[this.captureSetInfoId]
      if (!specs || specs.length === 0) {
        return null
      }
      
      // Sort specs by spec_index to maintain correct order
      const sortedSpecs = [...specs].sort((a, b) => {
        const indexA = a.spec_index !== undefined ? a.spec_index : 999
        const indexB = b.spec_index !== undefined ? b.spec_index : 999
        return indexA - indexB
      })
      
      return {
        captureSetId: this.captureSetInfoId,
        specs: sortedSpecs.map((spec) => ({
          index: spec.spec_index + 1,
          id: spec.id,
          freqRange: spec.freq_range ? `${spec.freq_range.freq_start} - ${spec.freq_range.freq_end}` : '-',
          center: spec.freq,
          span: spec.span || '-',
          margin: (spec.freq_range && spec.freq_range.margin > 0) ? spec.freq_range.margin : '-'
        }))
      }
    },

  })
})
