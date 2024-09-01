
export function calc_basic_auth_token(username, password) {
    return btoa(`${username}:${password}`);
}


