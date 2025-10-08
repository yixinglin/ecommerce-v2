export function getMapUrl(address: string, type: 'google' | 'baidu' = 'google'): string {
    const encoded = encodeURIComponent(address)

    if (type === 'baidu') {
        return `https://map.baidu.com/search/${encoded}`
    }

    return `https://www.google.com/maps/search/?api=1&query=${encoded}`
}
