// 用户上下文管理

import {createContext} from "react"

export interface User {
    id: number
    username: string
    email: string
    alias: string
    avatar: string
    phone: string
    gender: number
    signature: string
    birthday: string
    address: string
    country_code: string
    is_active: boolean
}

interface AuthContextType {
    user: User | null
    setUser: (u: User | null) => void
}

export const AuthContext = createContext<AuthContextType>({
    user: null,
    setUser: () => {
    },
})




