import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Estado de autenticación.
 *
 * El token vive únicamente aquí (persistido en 'auth-storage'). El
 * interceptor de axios lo lee con useAuthStore.getState().token, así que
 * no hay copias sueltas en localStorage que puedan quedar desfasadas.
 */
const useAuthStore = create(
    persist(
        (set) => ({
            user: null,
            token: null,
            role: null,

            setAuth: (user, token) =>
                set({
                    user,
                    token,
                    role: user?.role || null,
                }),

            clearAuth: () => {
                // Limpieza de las llaves sueltas que usaba la versión anterior.
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                set({ user: null, token: null, role: null })
            },
        }),
        {
            name: 'auth-storage',
        }
    )
)

export default useAuthStore
