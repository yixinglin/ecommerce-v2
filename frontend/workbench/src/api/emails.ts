import {get, post} from "@/utils/http.ts";
import type {ListResponse} from "@/api/orders.ts";

export interface PullEmailsPayload {
    limit: number
}

export const pullEmails = async (payload: PullEmailsPayload) => {
    return post<{"success_count": number}>(`/api/v1/reply_handler/pull`, payload)
}

export interface EmailQuery {
    status?: string;
    action_type?: string;
    category?: string;
    keyword?: string;
    page?: number;
    limit?: number;
}

export interface EmailResponse {
    id: number
    sender?: string
    sender_name?: string
    subject?: string
    received_at?: string
    category?: string
    status?: string
    action_type?: string
    recipient?: string
    body?: string
    ai_result_text?: string
}


export const listEmails = async (params?: Partial<EmailQuery>) => {
    return get<ListResponse<EmailResponse>>(`/api/v1/reply_handler/emails`, { params })
}

export const getEmail = (id: number) => {
    return get<EmailResponse>(`/api/v1/reply_handler/emails/${id}`)
}

export interface ProcessEmailPayload {
    category: string
    note: string
    old_email: string
    new_email: string
    user: string
}

export interface EmailActionResponse {
    id: number
    email_inbox_id: number
    action_type: string
    note: string
    old_email: string
    new_email: string
    user: string
    created_at: string
    updated_at: string
}

export const processEmail = async (email_id: number, payload: ProcessEmailPayload) => {
    return post<EmailResponse>(`/api/v1/reply_handler/emails/${email_id}/process`, payload)
}

export const analyzeEmail = async (email_id: number) => {
    return post<EmailResponse>(`/api/v1/reply_handler/emails/${email_id}/analyze`, {})
}

export const listEmailActions = async (email_inbox_id: number) => {
    return get<ListResponse<EmailActionResponse>>(`/api/v1/reply_handler/emails/${email_inbox_id}/actions`)
}


export const exportReport = async () => {
    const blob = await post<Blob>(`/api/v1/reply_handler/emails/report`, {}, {
        responseType: 'blob',
    })
    const filename = `report.xlsx`
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
}