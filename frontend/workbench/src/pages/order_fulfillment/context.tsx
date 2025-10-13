import React, {createContext, useContext, useEffect, useState} from "react";
import type { EnumResponse } from "@/api/orders.ts";
import { fetchEnums } from "@/api/orders.ts";

interface EnumsContextValue {
    enums: EnumResponse | null;
    loading: boolean;
    refresh: () => Promise<void>;
}

// 创建 Context
const OrderEnumsContext = createContext<EnumsContextValue>({
    enums: null,
    loading: false,
    refresh: async () => {},
});

// Provider
export const OrderEnumsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [enums, setEnums] = useState<EnumResponse | null>(null);
    const [loading, setLoading] = useState(false);

    const loadEnums = async () => {
        setLoading(true);
        try {
            const res = await fetchEnums();
            setEnums(res);
        } catch (err) {
            console.error("枚举加载失败", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadEnums(); // 初始化加载一次
    }, []);

    return (
        <OrderEnumsContext.Provider value={{ enums, loading, refresh: loadEnums }}>
            {children}
        </OrderEnumsContext.Provider>
    );
};

// Hook：在任意组件中使用
export const useOrderEnums = () =>  useContext(OrderEnumsContext);
