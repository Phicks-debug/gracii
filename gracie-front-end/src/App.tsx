import React, { useState, useRef, useEffect } from 'react'
import { Send, Paperclip } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: number
  text: string
  sender: 'user' | 'bot'
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      const userMessage: Message = { id: Date.now(), text: input, sender: 'user' }
      setMessages(prevMessages => [...prevMessages, userMessage])
      setInput('')
      setIsStreaming(true)

      try {
        const response = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: input }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        if (reader) {
          let botResponse = ''
          while (true) {
            const { value, done } = await reader.read()
            if (done) break
            const chunk = decoder.decode(value)
            botResponse += chunk
            setMessages(prevMessages => {
              const lastMessage = prevMessages[prevMessages.length - 1]
              if (lastMessage && lastMessage.sender === 'bot') {
                return [
                  ...prevMessages.slice(0, -1),
                  { ...lastMessage, text: botResponse },
                ]
              } else {
                return [
                  ...prevMessages,
                  { id: Date.now(), text: botResponse, sender: 'bot' },
                ]
              }
            })
          }
        }
      } catch (error) {
        console.error('Error:', error)
      } finally {
        setIsStreaming(false)
      }
    }
  }

  const handleAttachment = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log('File selected:', file.name)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-dark-gray text-white">
      <header className="bg-darker-gray p-4 text-center">
        <h1 className="text-2xl font-bold">Gracie</h1>
      </header>
      <main className="flex-1 overflow-auto p-4 pb-0">
        <div className="max-w-3xl mx-auto">
          {messages.map((message) => (
            <div key={message.id} className={`flex items-start mb-4 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex items-start space-x-2 ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {message.sender === 'bot' && (
                  <div className="p-2 rounded-lg bg-gray-700">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold">AI</span>
                    </div>
                  </div>
                )}
                <div className={`p-3 rounded-lg ${message.sender === 'user' ? 'bg-user-gray max-w-md' : ''} ${message.sender === 'user' ? 'text-white' : 'text-white'}`}>
                  {message.sender === 'user' ? (
                    <div className="break-words">{message.text}</div>
                  ) : (
                    <ReactMarkdown className="prose prose-invert max-w-none">
                      {message.text}
                    </ReactMarkdown>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </main>
      <footer className="p-4 pt-0 bg-dark-gray">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="relative flex items-center">
            <button 
              type="button"
              onClick={handleAttachment}
              className="absolute left-2 text-gray-400 hover:text-white focus:outline-none"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
            />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="w-full p-3 pl-10 pr-12 rounded-lg bg-darker-gray text-white focus:outline-none shadow-lg transition-shadow duration-300 ease-in-out focus:shadow-xl"
              disabled={isStreaming}
            />
            <button 
              type="submit" 
              className="absolute right-2 text-gray-400 hover:text-white focus:outline-none"
              disabled={isStreaming}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
      </footer>
    </div>
  )
}

export default App