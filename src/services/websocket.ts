type MessageHandler = (data: any) => void

class WebSocketManager {
  public ws: WebSocket | null = null
  private url: string
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(type: 'document' | 'spreadsheet', id: number) {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    this.url = `${protocol}://${window.location.host}/ws/${type}/${id}/`
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.emit('connected', {})
      }

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.emit(data.type, data)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emit('error', error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
        this.emit('disconnected', {})
        this.reconnect()
      }
    } catch (error) {
      console.error('Failed to connect:', error)
      this.reconnect()
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => this.connect(), 5000 * this.reconnectAttempts)
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(event: string, handler: MessageHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)
  }

  off(event: string, handler: MessageHandler) {
    this.handlers.get(event)?.delete(handler)
  }

  private emit(event: string, data: any) {
    this.handlers.get(event)?.forEach((handler) => handler(data))
  }

  disconnect() {
    this.ws?.close()
  }
}

export default WebSocketManager
