// Simplified main.js without unnecessary delegates
document.addEventListener('alpine:init', () => {
  Alpine.data('main', function() {
    return {
      ready: false,
      // Initialization
      async init() {
        // Initialize stores with localStorage persistence
        Alpine.store('grid').init()
        Alpine.store('rms').init()
        Alpine.store('log').init()
        Alpine.store('image').init()
        
        // Load modular components dynamically with proper sequencing
          await this.loadComponentsSequentially()
          this.ready = true
          
          // Start refresh interval and get initial data
          await Alpine.store('app').startRefreshInterval()
        //Alpine.store('grid').getData()
      },

      // Special case setter for showing all grids with toggle logic
      set showAllGrids(value) {
        if (value !== Alpine.store('grid').showAll) {
          Alpine.store('grid').toggleShowAll()
        }
      },

      // Special case setter for modal close operation
      set show(value) {
        if (!value) Alpine.store('grid').closeModal()
      },

      // Special case setter for config modal close operation
      set showConfigModal(value) {
        if (!value) Alpine.store('config').closeModal()
      },

      // Handle zoom modal initialization from event
      zoomInit(zoomImageUrl, modalTitle) {
        Alpine.store('grid').initZoom(zoomImageUrl, modalTitle)
      },
      
      // Load components sequentially to ensure proper timing
      async loadComponentsSequentially() {
        try {
          // Use Alpine.nextTick to ensure proper timing and avoid re-initialization
          await Alpine.nextTick()
          
          // Load the core components in parallel
          await Promise.all([
            this.loadComponent('status-box'),
            this.loadComponent('rms-data-table'),
            this.loadComponent('config-modal'),
            this.loadComponent('grid-view'),
            this.loadComponent('log-view'),
          ])

          
          // Wait for Alpine to process the new components, then load nested ones
          await Alpine.nextTick()
          await this.loadComponent('rms-thresholds')
          await this.loadComponent('config-values')

          
        } catch (error) {
          console.error('Error loading components:', error)
        }
      },
      
      // Load any component dynamically by name
      async loadComponent(componentName) {
        try {
          //const response = await fetch(`./assets/components/${componentName}.html`, { cache: 'reload' })
          const response = await fetch(`./assets/components/${componentName}.html`)
          if (response.ok) {
            const html = await response.text()
            const placeholder = document.getElementById(`${componentName}-placeholder`)
            if (placeholder) {
              placeholder.innerHTML = html
            } else {
              console.warn(`${componentName} placeholder not found`)
            }
          } else {
            console.warn(`Could not load ${componentName} component`)
          }
        } catch (error) {
          console.error(`Error loading ${componentName} component:`, error)
        }
      }
    }
  })
})
