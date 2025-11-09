import dayjs from "dayjs";

export const formatTime = (value: string) => {
    return dayjs(value).format('DD.MM.YYYY HH:mm')
}

export const formatDate = (value: string) => {
    return dayjs(value).format('DD.MM.YYYY')
}

export const formatWithPattern = (value: string, pattern: string) => {
    return dayjs(value).format(pattern)
}