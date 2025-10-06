
// 用户上下文管理

import { createContext } from "react"

export interface User {
    id: number
    username: string
    email: string
    alias: string
    avatar: string
    is_active: boolean
}

interface AuthContextType {
    user: User | null
    setUser: (u: User | null) => void
}

export const AuthContext = createContext<AuthContextType>({
    user: null,
    setUser: () => {},
})




