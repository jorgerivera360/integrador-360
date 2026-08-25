import api from './api'

export const loginWithGoogle = (googleToken) => {
    return api.post('/auth/login', { google_token: googleToken })
}

export const getMe = () => {
    return api.get('/auth/me')
}