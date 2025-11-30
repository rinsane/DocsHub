import axios from 'axios'

// Helper function to get CSRF token from cookies
function getCookie(name: string): string | null {
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

const API = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies/CSRF
})

API.interceptors.request.use((config) => {
  // Get CSRF token from cookie
  const csrfToken = getCookie('csrftoken')
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

export const auth = {
  register: (username: string, email: string, password: string) =>
    API.post('/accounts/register/', { username, email, password }),
  login: (username: string, password: string) =>
    API.post('/accounts/login/', { username, password }),
  logout: () => API.post('/accounts/logout/'),
  getProfile: () => API.get('/accounts/profile/'),
}

export const documents = {
  list: () => API.get('/documents/'),
  create: (title: string) => API.post('/documents/create/', { title }),
  get: (id: number) => API.get(`/documents/${id}/`),
  update: (id: number, data: any) => API.post(`/documents/${id}/update/`, data),
  delete: (id: number) => API.post(`/documents/${id}/delete/`),
  addComment: (id: number, data: any) => API.post(`/documents/${id}/comment/`, data),
  getComments: (id: number) => API.get(`/documents/${id}/comments/`),
  share: (id: number, email: string, role: string = 'viewer') =>
    API.post(`/documents/${id}/permission/add/`, { email, role }),
  export: (id: number, format: string) => API.get(`/documents/${id}/export/${format}/`),
  import: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return API.post(`/documents/${id}/import/`, form)
  },
}

export const spreadsheets = {
  list: () => API.get('/spreadsheets/'),
  create: (title: string) => API.post('/spreadsheets/create/', { title }),
  get: (id: number) => API.get(`/spreadsheets/${id}/`),
  update: (id: number, data: any) => API.post(`/spreadsheets/${id}/update/`, data),
  delete: (id: number) => API.post(`/spreadsheets/${id}/delete/`),
  share: (id: number, email: string, role: string) =>
    API.post(`/spreadsheets/${id}/permission/add/`, { email, role }),
  export: (id: number, format: string) => API.get(`/spreadsheets/${id}/export/${format}/`),
}

export const notifications = {
  list: () => API.get('/notifications/'),
  markAsRead: (id: number) => API.post(`/notifications/${id}/read/`),
  unreadCount: () => API.get('/notifications/unread-count/'),
}

export default API
