import {type ReactNode, useEffect, useState} from 'react'
import Cookies from 'js-cookie'
import {getUserInfo} from '@/api/user'
import {AuthContext, type User} from '@/context/AuthContext'


export const AuthProvider = ({children}: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState<boolean>(true)

    useEffect(() => {
        const token = localStorage.getItem('token') || Cookies.get('token')
        if (token) {
            getUserInfo()
                .then(setUser)
                .catch(() => {
                    setUser(null)
                    localStorage.removeItem('token')
                    Cookies.remove('token')
                }).finally(() => {
                    setLoading(false)
                })
        } else {
            setLoading(false)
        }
    }, [])

    if (loading) {
        return <div>Authenticating...</div>
    }

    return (
        <AuthContext.Provider value={{user, setUser}}>
            {children}
        </AuthContext.Provider>
    )
}
