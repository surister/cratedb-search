export async function hybrid_search(search_term) {
    return await fetch(
        'http://localhost:8000' + '/search/hybrid?search_term=' + search_term
    )
}