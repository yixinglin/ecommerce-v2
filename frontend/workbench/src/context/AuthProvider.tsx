import { type ReactNode, useEffect, useState } from 'react'
import Cookies from 'js-cookie'
import { getUserInfo } from '@/api/user'
import { AuthContext, type User } from '@/context/AuthContext'


export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null)

    useEffect(() => {
        const token = localStorage.getItem('token') || Cookies.get('token')
        if (token) {
            getUserInfo().then(setUser).catch(() => setUser(null))
        }
    }, [])

    return (
        <AuthContext.Provider value={{ user, setUser }}>
            {children}
        </AuthContext.Provider>
    )
}
