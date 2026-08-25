import useAuthStore from '@/store/authStore'

const useHasRole = (roles) => {
    const role = useAuthStore((state) => state.role)
    return roles.includes(role)
}

export default useHasRole