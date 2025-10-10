import dayjs from "dayjs";

export const formatTime = (value: string) => {
    return dayjs(value).format('DD.MM.YYYY HH:mm')
}