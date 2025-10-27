// Log Data Store - handles fetching and displaying processing logs
document.addEventListener('alpine:init', () => {
  Alpine.store('log', {
    // Initialize state
    init() {

    },

    // State
    data: [],
    dataLoading: false,
    dataError: '',

    // Filters
    idFilter: '',
    typeFilter: '',

    // Distinct option lists
    distinctIds: [],
    distinctTypes: [],

    dataFiltered: [],


    // Actions
    async getData() {
      try {
        this.dataLoading = true
        this.dataError = ''

        const id = Alpine.store('app').currentCaptureSetId
        const response = await fetch(`/log_data?capture_set_id=${encodeURIComponent(id)}`)
        if (response.ok) {
          const data1 = await response.json()
          const data = data1.data

          this.data = data || []
          // Recompute distinct option lists
          const uniq = (arr) => Array.from(new Set(arr.filter(v => typeof v === 'string' && v.trim() !== '')))
          this.distinctIds = uniq((this.data || []).map(r => (r && r.id) ? String(r.id) : '')).sort()
          this.distinctTypes = uniq((this.data || []).map(r => (r && r.type) ? String(r.type) : '')).sort()

        } else {
          const errorData = await response.json().catch(() => ({}))
          this.dataError = errorData.error || 'Failed to load logs'
        }
      } catch (error) {
        console.error('Error loading logs:', error)
        this.dataError = 'Error loading logs: ' + error.message
      } finally {
        this.setFilteredData()

        this.dataLoading = false
      }
    },
    setFilteredData() {
      const idf = this.idFilter
      const tf = this.typeFilter
      if (!idf && !tf) {
          this.dataFiltered = this.data
      } else {
          this.dataFiltered = (this.data || []).filter(row => {
            const okId = !idf || String(row.id) === idf
            const okType = !tf || String(row.type) === tf
            return okId && okType
          })
      }
    }

  })
})

