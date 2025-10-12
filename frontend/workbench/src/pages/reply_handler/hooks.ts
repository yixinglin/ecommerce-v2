import {useRequest} from "@/hooks/useRequest.ts";
import {listEmails, type EmailResponse, type EmailQuery, getEmail} from '@/api/emails.ts';
import {useState} from "react";
import {type ListResponse} from "@/api/orders.ts";


export function useEmails(initialParams: EmailQuery = {page: 1, limit: 10}) {

    const [emails, setEmails] = useState<EmailResponse[]>([]);
    const [params, setParams] = useState<EmailQuery>(initialParams);

    const {
        data,
        loading,
        run: runList,
    } = useRequest<ListResponse<EmailResponse>, EmailQuery>(listEmails, {
        manual: true,
        defaultParams: initialParams,
        onSuccess: (res) => {
            if (res?.data) setEmails(res.data)
        },
    })

    const fetchEmails = async (query?: Partial<EmailQuery>, resetPage = false) => {
        const merged = { ...params, ...query }
        if (resetPage) merged.page = 1
        setParams(merged)
        await runList(merged)
    }

    const refreshEmail = async (id: number) => {
        const res = await getEmail(id)
        if (res) {
            setEmails((prev) => prev.map((o) => (o.id === id ? res : o)))
        }
    }

    const resetEmails = async  () => {
        setParams(initialParams)
        await runList(initialParams)
    }

    const pagination = {
        current: data?.page || params.page || 1,
        pageSize: data?.limit || params.limit || 10,
        total: data?.total || 0,
        showTotal: (total: any) => `共 ${total} 条`,
        showSizeChanger: true,
        onChange: (page: number, limit: number) => {
            fetchEmails({ page, limit })
        },
    }

    return {
        emails,
        loading,
        pagination,
        fetchEmails,
        refreshEmail,
        resetEmails,
    }

}