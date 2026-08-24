import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Estado de interfaz que debe sobrevivir a recargas.
 * Por ahora solo el colapso del sidebar.
 */
const useUiStore = create(
    persist(
        (set) => ({
            sidebarColapsado: false,

            toggleSidebar: () =>
                set((state) => ({ sidebarColapsado: !state.sidebarColapsado })),

            setSidebarColapsado: (colapsado) => set({ sidebarColapsado: colapsado }),
        }),
        {
            name: 'ui-storage',
        }
    )
)

export default useUiStore
